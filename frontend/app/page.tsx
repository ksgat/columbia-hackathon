import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 bg-background">
      <main className="flex flex-col items-center gap-10 text-center">
        <div className="flex flex-col gap-3">
          <h1 className="text-7xl font-bold tracking-tighter leading-none">
            Bet on Your Friends
          </h1>
          <p className="text-xl text-muted-foreground font-medium tracking-tight">
            Create prediction markets and see what your friends really think
          </p>
        </div>
        
        <Link href="/create">
          <Button size="lg" className="gap-2">
            <Plus className="h-5 w-5" />
            Create Market
          </Button>
        </Link>
      </main>
    </div>
  );
}
