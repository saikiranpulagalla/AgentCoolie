import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { Bot, Check, CheckCircle2, CreditCard, Shield, Sparkles, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { activateDemoAutopilot, getBillingPlan } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const highlights = [
  "1,000 AI chat messages per month",
  "250 web searches per month",
  "75 active tasks and 200 task executions",
  "50 Gmail send/reply actions per month",
  "250 WhatsApp messages per month",
  "10 call reminders per month",
  "25 PDF pages per upload",
  "15-turn short memory per chat",
];

export default function Checkout() {
  const { user, loading } = useAuth();
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState(false);
  const [currentPlan, setCurrentPlan] = useState<string>("companion");

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const summary = await getBillingPlan();
        setCurrentPlan(summary?.plan?.id || "companion");
        if (summary?.plan?.id === "autopilot") {
          setSuccess(true);
        }
      } catch (e) {
        console.warn("Could not load billing plan", e);
      }
    })();
  }, [user?.uid]);

  const handlePay = async () => {
    if (!user) {
      setLocation("/login");
      return;
    }

    setProcessing(true);
    try {
      const summary = await activateDemoAutopilot();
      setCurrentPlan(summary?.plan?.id || "autopilot");
      setSuccess(true);
      window.dispatchEvent(new CustomEvent("agentcoolie:plan-updated", { detail: summary }));
      toast({
        title: "Autopilot activated",
        description: "Your AgentCoolie account is now in Pro mode.",
      });
    } catch (err: any) {
      toast({
        title: "Upgrade failed",
        description: err?.message || "Could not activate Autopilot.",
        variant: "destructive",
      });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen app-surface flex items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-auto app-surface">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />
      <div className="relative mx-auto grid min-h-screen max-w-6xl gap-8 px-5 py-10 lg:grid-cols-[.9fr_1.1fr] lg:items-center">
        <div className="space-y-7">
          <Link href="/">
            <div className="inline-flex items-center gap-3">
              <div className="agent-mark flex h-11 w-11 items-center justify-center rounded-lg bg-primary shadow-lg shadow-primary/20">
                <Bot className="relative z-10 h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">AgentCoolie</span>
            </div>
          </Link>

          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border bg-card px-4 py-2 text-sm font-medium text-primary">
              <Sparkles className="h-4 w-4" />
              Autopilot checkout
            </div>
            <h1 className="text-5xl font-bold leading-tight md:text-6xl">
              Upgrade to AgentCoolie Autopilot
            </h1>
            <p className="max-w-xl text-lg leading-8 text-muted-foreground">
              Unlock deeper memory, higher task limits, Gmail automation, WhatsApp access, call reminders, and larger file handling.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { icon: Zap, label: "More automation" },
              { icon: Shield, label: "Backend-enforced" },
              { icon: CreditCard, label: "Demo checkout" },
            ].map((item) => (
              <div key={item.label} className="rounded-lg border bg-card/80 p-4">
                <item.icon className="mb-3 h-6 w-6 text-primary" />
                <p className="font-semibold">{item.label}</p>
              </div>
            ))}
          </div>
        </div>

        <Card className="relative overflow-hidden border-2 p-8 shadow-xl">
          <div className="absolute inset-x-0 top-0 h-1.5 bg-primary" />
          {!success ? (
            <div className="space-y-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-primary">AgentCoolie Autopilot</p>
                  <div className="mt-2 flex items-end gap-2">
                    <span className="text-5xl font-bold">Rs. 499</span>
                    <span className="pb-2 text-muted-foreground">/ month</span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">$6/month outside India</p>
                </div>
                <div className="rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
                  Pro mode
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {highlights.map((item) => (
                  <div key={item} className="flex items-start gap-3 rounded-lg bg-muted/45 p-3">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span className="text-sm">{item}</span>
                  </div>
                ))}
              </div>

              <div className="rounded-lg border bg-background/70 p-4 text-sm text-muted-foreground">
                This is a demo checkout. No real payment is collected. Clicking Pay activates Autopilot for this account in Supabase.
              </div>

              <Button
                size="lg"
                onClick={handlePay}
                disabled={processing || currentPlan === "autopilot"}
                className="w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {processing ? "Processing..." : currentPlan === "autopilot" ? "Already on Autopilot" : "Pay and Activate Autopilot"}
                <CreditCard className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <div className="flex min-h-[520px] flex-col items-center justify-center text-center">
              <div className="relative mb-8">
                <div className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
                <div className="relative flex h-32 w-32 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-2xl shadow-primary/30">
                  <CheckCircle2 className="h-20 w-20 animate-in zoom-in duration-700" />
                </div>
              </div>
              <h2 className="text-4xl font-bold">You are now in Autopilot mode</h2>
              <p className="mt-4 max-w-md leading-7 text-muted-foreground">
                AgentCoolie Pro limits are active for this account. You can now use higher automation, memory, search, Gmail, WhatsApp, calls, and file limits.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Link href="/chat">
                  <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                    Start Using Autopilot
                  </Button>
                </Link>
                <Link href="/settings">
                  <Button variant="outline">View Plan</Button>
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
