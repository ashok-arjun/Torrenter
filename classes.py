class Block:

	BlockMissing = 0
	BlockPresent = 1
	BlockPending = 2

	def __init__(self, piece_index, block_offset, block_length):
		self.piece_index = piece_index
		self.offset = block_offset
		self.block_length = block_length
		self.state = Block.BlockMissing
		self.data = b''


class Piece:

	PieceMissing = 0
	PiecePresent = 1
	PiecePending = 2

	def __init__(self, piece_hash, piece_index, blocks):
		self.index = piece_index
		self.hash = piece_hash
		self.blocks = blocks
		self.state = Piece.PieceMissing

	def _get_next_block(self):
		#return the next missing block in the blocks list

	def _receive_block(self, block):
		#receive the block, store the data with the offset in the particular index of this piece


class PieceManager:
	def __init__(self, pieces_hash, piece_length, total_length, file_name):
		self.pieces_hash = pieces_hash
		self.piece_length = piece_length
		self.total_length = total_length
		self.file_name = file_name
		self.peers = {}
		self.pieces = []
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


			self.pieces.append(Piece(piece_hash,piece_index,blocks))


	def _add_peer(self, peer_id):
		#add peer called from PeerConnection, called with empty bitfield, then bitfield is added later

	def update_peer(self,peer_id):
		#set the peer's bitfield

	def _get_next_piece(self, peer_id):
		#get the next piece of this particular peer by decoding the bitfield

	def _receive_block(self, peer_id, piece_index, block_offset, data):
		#receive the block, and mark it completed in the piece, and check if the piece is over and hash is matching

	def _peer_connection_closed(self, peer_id):
		#delete the blocks of the peer's piece and 
