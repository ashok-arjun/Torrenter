import asyncio
import aiofiles as aiof
import os
from time import time 
from hashlib import sha1

class Block:

	BlockMissing = 0
	BlockPresent = 1

	def __init__(self, piece_index, block_offset, block_length,data = b''):
		self.piece_index = piece_index
		self.offset = block_offset
		self.block_length = block_length
		self.state = Block.BlockMissing
		self.data = data

	def _clear_block(self):
		self.state = Block.BlockMissing
		self.data = b''

class Piece:


	def __init__(self, piece_hash, piece_index, piece_length, blocks, files):
		self.index = piece_index
		self.hash = piece_hash
		self.blocks = blocks
		self.length = piece_length
		self.files = files
		self.sending_peer = None

	def _get_next_block(self):
		"""
		Return: the next block in order for the piece
		"""

		for block in self.blocks:
			if block.state == Block.BlockMissing:
				return block
		return None
	
	def _receive_block_from_response(self, response_message):
		"""
		Decode the block offset, and store the data in the block and change the state to Present
		"""

		for block in self.blocks:
			if block.offset == response_message.block_offset:
				block.state = Block.BlockPresent
				block.data = response_message.block_data
				break
		return None

	def _clear_piece(self):
		[block._clear_block() for block in self.blocks]
		self.sending_peer = None

	def all_blocks_received(self):
		
		for block in self.blocks:
			if block.state == Block.BlockMissing:
				return False
		
		return True

	def hash_verified(self):
		computed_hash = sha1(self.data).digest()
		if computed_hash == self.hash:
			return True
		else:
			return False


	@property
	def data(self):
		total_data = b''
		for block in self.blocks:
			total_data += block.data
		return total_data


class PieceManager:
	def __init__(self, pieces_hash, piece_length, total_length, directory_name, files):
		self.pieces_hash = pieces_hash
		self.piece_length = piece_length
		self.total_length = total_length
		self.directory_name = directory_name
		self.peer_bitfields = {}
		self.missing_pieces = []
		self.ongoing_pieces = []
		self.full_pieces = []

		self.files = files

		self.start_time = time()
		self.downloaded_bytes = 0
		self._initialise_pieces()

	async def initialise_file_pointers(self):

		self.file_pointers = []

		if len(self.files) > 1:
			os.makedirs(self.directory_name,exist_ok=True)	

		for file in self.files:
			parent_dir = os.path.dirname(file['path'])
			if parent_dir != b'':
				os.makedirs(parent_dir,exist_ok=True)
			mode = 'rb+' if os.path.exists(file['path']) else 'wb+'
			self.file_pointers.append(await aiof.open(file['path'],mode))

	def _initialise_pieces(self):

		unconsumed_files = self.files[:]
		consumed_files = []

		for piece_index,piece_hash in enumerate(self.pieces_hash):

			piece_length = self.piece_length if piece_index < len(self.pieces_hash) - 1 else self.total_length - piece_offset
			blocks = []
			block_size = 2 ** 14
			block_index = 0
			more_blocks = True
			while(more_blocks):
				block_offset = block_index * block_size
				if block_offset + block_size < piece_length:
					block = Block(piece_index,block_offset,block_size)
				else:
					#last block
					block = Block(piece_index,block_offset,piece_length - block_offset)
					more_blocks = False
				blocks.append(block)
				block_index += 1

			piece_offset = 0
			piece_files = []

			for f in unconsumed_files[:]:

				
				piece_remaining_length = piece_length - piece_offset
				if(piece_remaining_length <= 0):
					break

				file_remaining_length = f['length'] - f['offset']
				
				if file_remaining_length > piece_remaining_length:
					piece_files.append({'index':f['index'],'offset':f['offset'],'length':piece_remaining_length})
					f['offset'] += piece_remaining_length
					piece_offset += piece_remaining_length
				
				elif file_remaining_length <= piece_remaining_length:
					piece_files.append({'index':f['index'],'offset':f['offset'],'length':file_remaining_length})
					f['offset'] += file_remaining_length
					piece_offset += file_remaining_length
					unconsumed_files.remove(f)
					consumed_files.append(f)

			self.missing_pieces.append(Piece(piece_hash,piece_index,piece_length,blocks,piece_files))
			

	def update_peer(self,peer_id, bitfield = b'', have = -1):
		if(bitfield != b''):
			self.peer_bitfields[peer_id] = bitfield
		if(have != -1):
			self.peer_bitfields[peer_id][have] = 1
	def next_request(self, peer_id):
		"""
		1. Check for ongoing pieces
		3. If no, get the next piece for the peer
		4. Get the next block for that piece
		5. Return that block

		Return none, if no block can be requested for this peer
		"""
		piece = self._ongoing_piece(peer_id)
		if not piece:
			piece = self._next_piece(peer_id)
		return piece._get_next_block()		

		

	def _ongoing_piece(self, peer_id):
		"""
		returns the peer's ongoing piece or NULL
		"""
		for piece in self.ongoing_pieces:
			if piece.sending_peer == peer_id:
				return piece
		return None
		 

	def _next_piece(self,peer_id):
		"""
		returns the next piece that can be requested from the peer AND transfer it to ongoing
		"""
		for i,piece in enumerate(self.missing_pieces):
			if self.peer_bitfields[peer_id][piece.index]:
				piece = self.missing_pieces.pop(i)
				self.ongoing_pieces.append(piece)
				piece.sending_peer = peer_id
				return piece
		return None


	def _check_block_integrity(self, response, request):
		"""
		Checks if the requested parameters are satisfied in the received block
		:return True if satisfied, False otherwise
		"""
		if (response.piece_index == request.pieceIndex) and (response.block_offset == request.blockOffset) and (len(response.block_data) == request.blockLength):
			return True
		else:
			return False

	async def _receive_block(self, message, corresponding_request):
		"""
		This is called from PeerConnection, whenever a Block is received.

		1. Check block integrity
		2. Access the piece, and persist the block onto the piece(using Piece._receive_block)
		3. Check if the piece is complete
		4. If yes, compute the hash of the piece and compare it with the actual_hash, and if they are equal, transfer piece from ongoing_pieces to full_pieces write the piece to memory
		"""
		#1
		if self._check_block_integrity(message, corresponding_request) == False:
			# print('This block does not correspond to the previous request. Rejecting it.')
			return None


		#2
		flag = False
		for ongoing_index,piece in enumerate(self.ongoing_pieces):
			if piece.index == message.piece_index:
				flag = True
				break

		if flag == False:
			# print('No ongoing piece corresponds to the recieved piece')
			return None

		self.downloaded_bytes += len(message.block_data)
		piece._receive_block_from_response(message)
		#3 & 4
		if piece.all_blocks_received():
			if piece.hash_verified():
				self.ongoing_pieces.pop(ongoing_index)
				self.full_pieces.append(piece)
				await self.write_piece_to_file(piece)
				# print('Finished writing piece to file',piece.index)
			else:
				piece._clear_piece()
				self.ongoing_pieces.pop(ongoing_index)
				self.missing_pieces.append(piece)


	async def write_piece_to_file(self, piece):
		data_offset = 0
		for file in piece.files:
			file_index = file['index']
			file_offset = file['offset']
			file_length = file['length']
			file_pointer = self.file_pointers[file_index]
			await file_pointer.seek(file_offset,0)
			await file_pointer.write(piece.data[data_offset:data_offset + file_length])
			data_offset += file_length

	def _peer_connection_closed(self, peer_id, pending_request):
		"""
		Remove the peer from the peer dictionary, and if there is a pending request for the peer, decode the request, transfer 
		that PIECE from pending to missing, clear the piece.
		"""
		self.peer_bitfields.pop(peer_id,None)
		for i,piece in enumerate(self.ongoing_pieces):
			if piece.index == pending_request.pieceIndex:
				piece._clear_piece()
				self.ongoing_pieces.pop(i)
				self.missing_pieces.append(piece)
				break
		return None

	def get_download_speed(self):
		seconds_elapsed = time() - self.start_time
		return self.downloaded_bytes/seconds_elapsed	


	@property
	def complete(self):
		return len(self.full_pieces) == len(self.pieces_hash)

	@property
	def percentage_complete_pieces(self):
		return len(self.full_pieces) * 100 / len(self.pieces_hash)

	@property
	def uploaded_bytes(self):
		return 0