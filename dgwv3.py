from blocktools import *

def DarkGravityWave3(blockList, params):
	bnPowLimit = bigNumFromCompact(params.bnPowLimit)
	nPastBlocks = 24

	lastBlock = blockList[0]

	for nCountBlocks in range(1, nPastBlocks):
		bnTarget = bigNumFromCompact(blockList[nCountBlocks].nBits)
		if nCountBlocks ==1:
			bnPastTargetAvg = bnTarget
		else:
			bnPastTargetAvg = (bnPastTargetAvg * nCountBlocks + bnTarget) / (nCountBlocks + 1)

	bnNew = bnPastTargetAvg

	nActualTimespan = lastBlock.getBlockTime() - blockList[nPastBlocks-1].getBlockTime()
	nTargetTimespan = nPastBlocks * params.nPowTargetSpacing

	if nActualTimespan < nTargetTimespan/3:
		nActualTimespan = nTargetTimespan/3
	if nActualTimespan > nTargetTimespan*3:
		nActualTimespan = nTargetTimespan*3

	bnNew *= nActualTimespan
	bnNew /= nTargetTimespan

	if bnNew > bnPowLimit:
		bnNew = bnPowLimit


	return compactFromBigNum(bnNew)