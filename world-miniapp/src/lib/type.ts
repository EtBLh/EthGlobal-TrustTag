export type proposal = {
	//chain_id: string
	_id: string
	address: string
	tag: 'normal_user' | 'gamble' | 'exchange' | 'scam'
}