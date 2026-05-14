import { Link } from "wouter";
import {
  ArrowRight,
  Bell,
  Bot,
  Brain,
  CalendarClock,
  CheckCircle2,
  Clock,
  CreditCard,
  FileText,
  Globe,
  MessageSquare,
  Play,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const featureCards = [
  {
    icon: Brain,
    title: "Remembers useful context",
    text: "Tell AgentCoolie your goals, college, exam plans, or preferences once, then use that context in later chats.",
  },
  {
    icon: CalendarClock,
    title: "Automates timed tasks",
    text: "Schedule reminders or action requests like opening a YouTube song, checking a site, or following up on work.",
  },
  {
    icon: Search,
    title: "Finds current answers",
    text: "Ask about recent news, live topics, or fresh information and get source-backed results inside chat.",
  },
  {
    icon: FileText,
    title: "Understands files and images",
    text: "Attach screenshots, images, PDFs, or audio and ask the assistant to explain, summarize, or help act on them.",
  },
];

const workflow = [
  "You ask a normal question or schedule an action",
  "AgentCoolie uses remembered context when it helps",
  "It searches current sources when the answer needs freshness",
  "You get a useful answer, reminder, or action result",
];

const previewSteps = [
  "Remembers your exam and study goals",
  "Searches current news when needed",
  "Schedules the follow-up task",
  "Responds with clear next steps",
];

const plans = [
  {
    name: "AgentCoolie Companion",
    price: "Free",
    description: "For trying the personal agent with light daily usage.",
    features: [
      "150 chat messages/month",
      "25 web searches/month",
      "5 active tasks",
      "15 long-term memories",
      "1 call reminder/month",
      "Gmail and WhatsApp not included",
    ],
    cta: "Start Free",
    href: "/login",
    accent: false,
  },
  {
    name: "AgentCoolie Autopilot",
    price: "Rs. 499/month",
    description: "For deeper memory, more automation, Gmail, WhatsApp, calls, and larger files.",
    features: [
      "1,000 chat messages/month",
      "250 web searches/month",
      "75 active tasks",
      "200 long-term memories",
      "10 call reminders/month",
      "Gmail + WhatsApp automation",
    ],
    cta: "Upgrade to Autopilot",
    href: "/checkout",
    accent: true,
  },
];

function AgentPreview() {
  return (
    <div className="landing-reel w-full rounded-lg border border-white/16 bg-black/42 p-4 text-white shadow-2xl backdrop-blur-xl">
      <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2 text-sm text-white/80">
          <span className="h-2.5 w-2.5 rounded-full bg-primary" />
          Live Agent Preview
        </div>
        <div className="text-xs text-white/55">memory + search + tasks</div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.08fr_.92fr]">
        <div className="space-y-3">
          <div className="landing-chat-line ml-auto w-[78%] rounded-lg bg-primary p-3 text-sm font-medium text-primary-foreground">
            Remember that I am preparing for IAS and need Tamil Nadu politics updates.
          </div>
          <div className="landing-chat-line landing-delay-1 w-[82%] rounded-lg bg-white/12 p-3 text-sm text-white/90">
            Got it. I will use that context when you ask for current affairs.
          </div>
          <div className="landing-chat-line landing-delay-2 ml-auto w-[88%] rounded-lg bg-primary p-3 text-sm font-medium text-primary-foreground">
            Tomorrow 8 AM: remind me to review today&apos;s state politics news.
          </div>
        </div>

        <div className="grid gap-3">
          <div className="rounded-lg border border-white/12 bg-white/8 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium">
              <Brain className="h-4 w-4 text-primary" />
              Useful memory
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded-md bg-white/10 px-2.5 py-1">IAS preparation</span>
              <span className="rounded-md bg-white/10 px-2.5 py-1">Tamil Nadu politics</span>
              <span className="rounded-md bg-white/10 px-2.5 py-1">Study reminders</span>
            </div>
          </div>

          <div className="rounded-lg border border-white/12 bg-white/8 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium">
              <CalendarClock className="h-4 w-4 text-primary" />
              Scheduled action
            </div>
            <div className="flex items-center gap-3 rounded-md bg-white/10 p-3">
              <Clock className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-semibold">8:00 AM review</p>
                <p className="text-xs text-white/62">Current affairs follow-up</p>
              </div>
            </div>
          </div>

          <div className="space-y-3 rounded-lg border border-white/12 bg-white/8 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Sparkles className="h-4 w-4 text-primary" />
              What happens next
            </div>
            {previewSteps.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/18 text-xs text-primary">
                  {index + 1}
                </div>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/12">
                  <div className="landing-meter h-full rounded-full bg-primary" style={{ animationDelay: `${index * 220}ms` }} />
                </div>
                <span className="w-36 text-xs text-white/72">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen overflow-auto bg-background text-foreground">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-black/48 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 text-white">
          <Link href="/">
            <div className="flex items-center gap-3">
              <div className="agent-mark flex h-10 w-10 items-center justify-center rounded-lg bg-primary shadow-lg shadow-primary/30">
                <Bot className="relative z-10 h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">AgentCoolie</span>
            </div>
          </Link>

          <nav className="hidden items-center gap-6 text-sm text-white/78 md:flex">
            <a href="#features" className="transition-colors hover:text-white">Features</a>
            <a href="#workflow" className="transition-colors hover:text-white">Workflow</a>
            <a href="#pricing" className="transition-colors hover:text-white">Pricing</a>
            <a href="#about" className="transition-colors hover:text-white">About</a>
          </nav>

          <Link href="/login">
            <Button className="bg-white text-slate-950 hover:bg-white/90">Sign In</Button>
          </Link>
        </div>
      </header>

      <section className="relative min-h-[94vh] overflow-hidden bg-[#0f1117]">
        <div className="absolute inset-0 bg-grid-pattern opacity-[.12]" />
        <div className="absolute inset-x-0 top-0 h-2 bg-primary" />
        <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(220,38,38,.30),transparent_34%,rgba(255,255,255,.06)_70%,transparent)]" />

        <div className="relative mx-auto grid min-h-[94vh] max-w-7xl gap-10 px-5 pb-20 pt-28 lg:grid-cols-[.9fr_1.1fr] lg:items-center">
          <div className="max-w-4xl space-y-8 text-white">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-xl">
              <Play className="h-4 w-4 fill-white" />
              Personal AI agent for real daily work
            </div>

            <div className="space-y-5">
              <h1 className="text-6xl font-bold leading-none md:text-8xl">AgentCoolie</h1>
              <p className="max-w-2xl text-xl leading-8 text-white/84 md:text-2xl">
                Your assistant that remembers important context, finds current information, and helps automate tasks at the right time.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { icon: Brain, label: "Remembers you" },
                { icon: Search, label: "Searches live" },
                { icon: Bell, label: "Acts on time" },
              ].map((item) => (
                <div key={item.label} className="rounded-lg border border-white/14 bg-white/10 p-4 backdrop-blur-xl">
                  <item.icon className="mb-3 h-6 w-6 text-primary" />
                  <p className="font-semibold">{item.label}</p>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href="/login">
                <Button size="lg" className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                  Get Started
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="#about">
                <Button size="lg" variant="outline" className="border-white/30 bg-white/10 text-white hover:bg-white/18">
                  See What It Can Do
                </Button>
              </a>
              <Link href="/checkout">
                <Button size="lg" variant="outline" className="gap-2 border-white/30 bg-white/10 text-white hover:bg-white/18">
                  View Pro
                  <CreditCard className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>

          <AgentPreview />

          <div className="absolute bottom-5 left-1/2 hidden -translate-x-1/2 text-xs uppercase tracking-[0.28em] text-white/52 md:block">
            Scroll to explore
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-5 py-16">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="mb-2 text-sm font-semibold text-primary">What It Helps You Do</p>
            <h2 className="text-4xl font-bold">Less repeating yourself. More getting things done.</h2>
          </div>
          <p className="max-w-xl leading-7 text-muted-foreground">
            AgentCoolie is for students, creators, professionals, and anyone who wants one assistant to remember context, answer current questions, and manage follow-ups.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {featureCards.map((feature) => (
            <Card key={feature.title} className="group p-6 pressable">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary transition-transform group-hover:scale-105">
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
              <p className="leading-7 text-muted-foreground">{feature.text}</p>
            </Card>
          ))}
        </div>
      </section>

      <section id="workflow" className="border-y bg-card/70">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 lg:grid-cols-[.85fr_1.15fr] lg:items-center">
          <div className="space-y-4">
            <p className="text-sm font-semibold text-primary">How You Use It</p>
            <h2 className="text-4xl font-bold">Talk naturally. AgentCoolie handles the context.</h2>
            <p className="leading-7 text-muted-foreground">
              You do not need to think in commands. Ask like a person, then let the app connect memory, search, files, and reminders.
            </p>
          </div>

          <div className="grid gap-3">
            {workflow.map((item, index) => (
              <div key={item} className="pressable flex items-center gap-4 rounded-lg border bg-background p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  {index + 1}
                </div>
                <p className="font-medium">{item}</p>
                <CheckCircle2 className="ml-auto h-5 w-5 text-primary" />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-7xl px-5 py-16">
        <div className="mb-8 max-w-3xl space-y-3">
          <p className="text-sm font-semibold text-primary">Plans</p>
          <h2 className="text-4xl font-bold">Start free. Turn on Autopilot when you want the agent to do more.</h2>
          <p className="leading-7 text-muted-foreground">
            Companion is useful for light personal assistance. Autopilot unlocks higher limits for memory, live search, tasks, Gmail, WhatsApp, file analysis, and call reminders.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative overflow-hidden p-7 ${plan.accent ? "border-primary shadow-xl shadow-primary/10" : ""}`}
            >
              {plan.accent && <div className="absolute inset-x-0 top-0 h-1.5 bg-primary" />}
              <div className="mb-6 flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-primary">{plan.name}</p>
                  <h3 className="mt-2 text-4xl font-bold">{plan.price}</h3>
                  {plan.accent && <p className="mt-1 text-sm text-muted-foreground">$6/month outside India</p>}
                </div>
                {plan.accent && (
                  <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
                    Pro mode
                  </span>
                )}
              </div>
              <p className="mb-6 leading-7 text-muted-foreground">{plan.description}</p>
              <div className="mb-7 grid gap-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>
              <Link href={plan.href}>
                <Button className={plan.accent ? "w-full bg-primary text-primary-foreground hover:bg-primary/90" : "w-full"} variant={plan.accent ? "default" : "outline"}>
                  {plan.cta}
                </Button>
              </Link>
            </Card>
          ))}
        </div>
      </section>

      <section id="about" className="mx-auto max-w-7xl px-5 py-16">
        <div className="grid overflow-hidden rounded-lg border bg-card lg:grid-cols-[1fr_.8fr]">
          <div className="space-y-5 p-8 md:p-10">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm text-primary">
              <Bot className="h-4 w-4" />
              About the app
            </div>
            <h2 className="text-4xl font-bold">A personal agent that keeps track of the things you care about.</h2>
            <p className="leading-7 text-muted-foreground">
              AgentCoolie can help you study, follow news, remember important facts, open websites, analyze attachments, and schedule work. The goal is simple: reduce repeated effort and keep useful context close.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { icon: Globe, label: "Current answers" },
                { icon: Zap, label: "Action-ready" },
                { icon: Brain, label: "Context-aware" },
              ].map((item) => (
                <div key={item.label} className="rounded-lg border p-4">
                  <item.icon className="mb-3 h-6 w-6 text-primary" />
                  <p className="text-sm font-semibold">{item.label}</p>
                </div>
              ))}
            </div>
            <Link href="/login">
              <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                Continue to Login
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="bg-[#11141b] p-6 text-white">
            <div className="h-full min-h-[420px] rounded-lg border border-white/12 bg-white/8 p-5">
              <div className="mb-5 flex items-center gap-3">
                <div className="agent-mark flex h-11 w-11 items-center justify-center rounded-lg bg-primary">
                  <Bot className="relative z-10 h-5 w-5 text-primary-foreground" />
                </div>
                <div>
                  <p className="font-semibold">AgentCoolie can help with</p>
                  <p className="text-sm text-white/58">Study, news, tasks, files, and web actions</p>
                </div>
              </div>
              <div className="grid gap-3">
                {[
                  "Remember my college and exam goals",
                  "Summarize this screenshot or PDF",
                  "Open a YouTube song at 7 PM",
                  "Find recent Tamil Nadu politics news",
                  "Remind me before my assignment deadline",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 rounded-lg bg-white/10 p-3">
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                    <span className="text-sm text-white/86">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
