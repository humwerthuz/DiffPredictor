from blocktools import *
import requests, json
import cStringIO
import datetime
from dgwv3 import DarkGravityWave3

def work2Difficulty(bits):
    nShift = (bits >> 24) & 0xff
    dDiff = float(0x0000ffff) / (bits & 0x00ffffff)

    while nShift < 29:
        dDiff = dDiff * 256.0
        nShift = nShift +1

    while nShift > 29:
        dDiff = dDiff / 256.0
        nShift = nShift - 1

    return dDiff

class ConsensusParams(object):
    def __init__(self):
        pass

    @staticmethod
    def getParams():
        params = ConsensusParams()
        setattr(params, "nPowTargetTimespan", 30 * 60)
        setattr(params, "fPowNoRetargeting", False)
        setattr(params, "nPowTargetSpacing", 1 * 60)
        setattr(params, "bnPowLimit", 0x00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        return params

    def getDifficultyAdjustmentInterval(self):
        return self.nPowTargetTimespan / self.nPowTargetSpacing


class BlockHeader:
    def __init__(self, blockchain):
        self.version = reverseByteOrder(blockchain.read(8))
        self.previousHash = reverseByteOrder(blockchain.read(64))
        self.merkleHash = reverseByteOrder(blockchain.read(64))
        self.time = reverseByteOrder(blockchain.read(8))
        self.bits = reverseByteOrder(blockchain.read(8))
        self.nBits = int(self.bits, 16)
        self.nonce = reverseByteOrder(blockchain.read(8))

    def __str__(self):
        return str(self.toHumanReadable())

    def toHumanReadable(self):
        return {
            'version': int(self.version, 16),
            'prev_hash': self.previousHash,
            'merkleroot': self.merkleHash,
            'time': int(self.time,16),
            'diff_target': self.bits,
            'nonce': self.nonce,
            'difficulty': self.getDifficulty()
        }

    def getDifficulty(self):
        return work2Difficulty(self.nBits)

    def getBlockTime(self):
        return int(self.time, 16)
"""
unsigned int CalculateNextWorkRequired(const CBlockIndex* pindexLast, int64_t nFirstBlockTime, const Consensus::Params& params)
{
    // Limit adjustment step
    int64_t nActualTimespan = pindexLast->GetBlockTime() - nFirstBlockTime;
    if (nActualTimespan < params.nPowTargetTimespan/4)
        nActualTimespan = params.nPowTargetTimespan/4;
    if (nActualTimespan > params.nPowTargetTimespan*4)
        nActualTimespan = params.nPowTargetTimespan*4;

    // Retarget
    arith_uint256 bnNew;
    arith_uint256 bnOld;
    bnNew.SetCompact(pindexLast->nBits);
    bnOld = bnNew;
    // Chaucha: intermediate uint256 can overflow by 1 bit
    bool fShift = bnNew.bits() > 235;
    if (fShift)
        bnNew >>= 1;
    bnNew *= nActualTimespan;
    bnNew /= params.nPowTargetTimespan;
    if (fShift)
        bnNew <<= 1;

    const arith_uint256 bnPowLimit = UintToArith256(params.powLimit);
    if (bnNew > bnPowLimit)
        bnNew = bnPowLimit;

    return bnNew.GetCompact();
}
"""

def CalculateNextWorkRequired(pindexLast, pindexFirst, params):
    if(params.fPowNoRetargeting):
        return pindexLast.nBits

    nActualTimespan = float(pindexLast.getBlockTime()) - float(pindexFirst.getBlockTime())

    if (nActualTimespan < params.nPowTargetTimespan/4):
        nActualTimespan = params.nPowTargetTimespan/4
    if (nActualTimespan > params.nPowTargetTimespan*4):
        nActualTimespan = params.nPowTargetTimespan*4

    bnNew = bigNumFromCompact(pindexLast.nBits)
    bnOld = bnNew

    bnNew *= int(nActualTimespan)
    bnNew /= int(params.nPowTargetTimespan)

    if(bnNew > params.bnPowLimit):
        bnNew = int(params.bnPowLimit)

    return compactFromBigNum(bnNew)


def main():
    blockhashlist = []
    min_blocks = 30
    day_count = 3
    block_request_limit = 33  # could be 30, but my TOC...

    print "[*] Retrieving blocks for analysis..."

    for single_date in (datetime.datetime.now() - datetime.timedelta(n) for n in range(day_count)):
        query_str = "http://explorer.cha.terahash.cl/api/blocks?blockDate=%s&limit=%s" % (single_date.strftime("%Y-%m-%d"),block_request_limit)
        r = requests.get(query_str)
        _blocks = json.loads(r.text)['blocks']
        for _b in _blocks:
            blockhashlist.append(_b['hash'])
        print "\t- Found %d blocks when querying %s" % (len(_blocks), query_str)
        if len(blockhashlist) < min_blocks:
            print "\t+ We need at least %d blocks for analysis got %d, going back an extra day"  % (min_blocks, len(_blocks))
        else:
            break

    print "[*] Found a total of %d blocks when querying http://explorer.cha.terahash.cl" % (len(blockhashlist))

    print "[*] We have all the hashez! Now lets retreive the goodies (rawblocks)"

    rawblocks = []
    for blockhash in blockhashlist:
        r = requests.get("http://explorer.cha.terahash.cl/api/rawblock/%s" % blockhash)
        ioBuffer = cStringIO.StringIO()
        ioBuffer.write(json.loads(r.text)['rawblock'])
        ioBuffer.seek(0)
        rawblocks.append(BlockHeader(ioBuffer))

    print "[*] Got %s raw blocks" % len(rawblocks)

    rawblocks.sort(key=lambda x: x.getBlockTime(), reverse=True)
    assert(rawblocks[0].getBlockTime() > rawblocks[-1].getBlockTime())

    print "[*] Lets go find the last difficulty change..."
    
    blocksSinceLastDiffChange = 0
    lastdiff = rawblocks[0].getDifficulty()

    for block in rawblocks:
        diff = block.getDifficulty()
        if diff != lastdiff:
            print "[*] Gotcha! Last difficulty change %s blocks ago" % blocksSinceLastDiffChange
            break
        lastdiff = diff
        blocksSinceLastDiffChange = blocksSinceLastDiffChange + 1

    params = ConsensusParams.getParams()

    pLast = rawblocks[0]
    pFirst = rawblocks[blocksSinceLastDiffChange-1]
    #pFirst = rawblocks[1]

    print "===> Last block time: %s first block time: %s" % (pFirst.getBlockTime(), pLast.getBlockTime())

    expectedDifficulty = work2Difficulty(CalculateNextWorkRequired(pLast, pFirst, params))
    dgwExpectedDifficulty = work2Difficulty(DarkGravityWave3(rawblocks, params))

    print "===> Last block: difficulty %f, work: %d" % (pLast.getDifficulty(), pLast.nBits)
    print "===> If difficulty were to change now, it would be %f using standard method" % expectedDifficulty
    print "===> If difficulty were to change now, it would be %f using DGWv3" % dgwExpectedDifficulty

if __name__ == '__main__':
    main()
