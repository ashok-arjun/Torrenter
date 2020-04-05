class Block:

	BlockMissing = 0
	BlockPresent = 1

	def __init__(self, piece_index, block_offset, block_length):
		self.piece_index = piece_index
		self.offset = block_offset
		self.block_length = block_length
		self.state = Block.BlockMissing
		self.data = b''


class Piece:


	def __init__(self, piece_hash, piece_index, blocks):
		self.index = piece_index
		self.hash = piece_hash
		self.blocks = blocks

	def _get_next_block(self):
		"""
		Return: the next block in order for the piece
		"""
		pass

	def _receive_block(self, block):
		"""
		Decode the block offset, and store the data in the block and change the state to Missing
		"""
		pass


class PieceManager:
	def __init__(self, pieces_hash, piece_length, total_length, file_name):
		self.pieces_hash = pieces_hash
		self.piece_length = piece_length
		self.total_length = total_length
		self.file_name = file_name
		self.peer_bitfields = {}
		self.missing_pieces = []
		self.ongoing_pieces = []
		self.full_pieces = []
		self._initialise_pieces()


	def _initialise_pieces(self):
		"""
		For every piece in the total_length,

		initialise the piece with its index within the file, hash, length
		Now:
		Initialise the blocks with the offset within the piece, length and set the piece.blocks = to a list to Block instances

		Append the piece to PieceManager.pieces    
		"""

		for piece_index,piece_hash in enumerate(self.pieces_hash):
			piece_offset = piece_index * self.piece_length
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


			self.missing_pieces.append(Piece(piece_hash,piece_index,blocks))

	def update_peer(self,peer_id, bitfield):
		self.peer_bitfields[peer_id] = bitfield

	def next_request(self, peer_id):
		"""
		1. Check for ongoing pieces
		3. If no, get the next piece for the peer
		4. Get the next block for that piece
		5. Return that block

		Return none, if no block can be requested for this peer
		"""

		pass

	def _ongoing_piece(self, peer_id):
		"""
		returns the peer's ongoing piece or NULL
		"""
		
		pass 

	def _next_piece(self,peer_id):
		"""
		returns the next piece that can be requested from the peer
		"""
		pass	

	def _check_block_integrity(self, block, request):
		"""
		Checks if the requested parameters are satisfied in the received block
		:return True if satisfied, False otherwise
		"""
		pass

	def _receive_block(self, block):
		"""
		This is called from PeerConnection, whenever a Block is received.

		1. Check block integrity
		2. Access the piece, and persist the block onto the piece(using Piece._receive_block)
		3. Check if the piece is complete
		4. If yes, compute the hash of the piece and compare it with the actual_hash, and if they are equal, transfer piece from ongoing_pieces to full_pieces write the piece to memory
		"""
		pass

	def _peer_connection_closed(self, peer_id, pending_request):
		"""
		Remove the peer from the peer dictionary, and if there is a pending request for the peer, decode the request, transfer 
		that PIECE from pending to missing, clear the piece.
		"""
		pass
