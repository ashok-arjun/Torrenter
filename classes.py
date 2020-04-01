class Peer:
	def __init__(self, peer_id):
		self.id = peer_id
		self.ongoing_piece = None
		
	def _set_bitfield(self, bitfield):
		self.bitfield = bitfield

class Block:
	def __init__(self, piece_index, piece_offset, block_length):
		self.piece_index = piece_index
		self.piece_offset = piece_offset
		self.block_length = block_length
		self.state = 'Missing'
		self.data = b''


class Piece:
	def __init__(self, piece_hash, piece_index, piece_length):
		self.index = piece_index
		self.hash = piece_hash
		self.blocks = list() #split this
		self.piece_length = piece_length

	def _get_next_block(self):
		#return the next missing block in the blocks list

	def _receive_block(self, block):
		#receive the block, store the data with the offset in the particular index of this piece


class PieceManager:
	self.peers = list()
	self.pieces = list()

	def __init__(self, pieces):
		self.pieces = pieces

	def _add_peer(self, peer_id):
		self.peers.append(Peer(peer_id))
	
	def update_peer(self,peer_id):
		#set the peer's bitfield

	def _get_next_piece(self, peer_id):
		#get the next piece of this particular peer by decoding the bitfield

	def _receive_block(self, peer_id, piece_index, block_offset, data):
		#receive the block, and mark it completed in the piece, and check if the piece is over and hash is matching

	def _peer_connection_closed(self, peer_id):
		#delete the blocks of the peer's piece and 
