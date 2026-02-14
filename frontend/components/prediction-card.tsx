import Link from "next/link"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Prediction } from "@/types"
import { calculateOdds } from "@/lib/betting"

interface PredictionCardProps {
  prediction: Prediction
  marketId: string
}

export function PredictionCard({ prediction, marketId }: PredictionCardProps) {
  const { yesOdds, noOdds } = calculateOdds(prediction)
  const totalPool = prediction.yesPool + prediction.noPool

  return (
    <Card className="overflow-hidden border">
      <div className="p-5">
        <h3 className="text-base font-semibold mb-4 tracking-tight">{prediction.question}</h3>

        {/* Odds Display */}
        <div className="mb-4">
          <div className="flex h-10 rounded-md overflow-hidden border">
            <div
              className="bg-green-500/10 border-r border-green-500 flex items-center justify-center font-bold text-green-600 text-sm"
              style={{ width: `${yesOdds}%` }}
            >
              {yesOdds > 15 && `${yesOdds}%`}
            </div>
            <div
              className="bg-red-500/10 border-l border-red-500 flex items-center justify-center font-bold text-red-600 text-sm"
              style={{ width: `${noOdds}%` }}
            >
              {noOdds > 15 && `${noOdds}%`}
            </div>
          </div>
          
          <div className="flex justify-between mt-2 text-xs font-semibold">
            <span className="text-green-600">YES {yesOdds}%</span>
            <span className="text-red-600">NO {noOdds}%</span>
          </div>
        </div>

        {/* Pool Info */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground font-semibold">
            Pool: ${totalPool}
          </span>
          
          <Link href={`/market/${marketId}/prediction/${prediction.id}`}>
            <Button size="sm">
              Place Bet
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  )
}
