import { Link } from "wouter";
import { Bell, Bot, Brain, CalendarClock, CheckCircle2, FileText, Globe, MessageSquare, Search, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

const pillars = [
  {
    icon: MessageSquare,
    title: "Ask naturally",
    text: "Use normal language for chat, file questions, website requests, YouTube actions, reminders, and planning.",
  },
  {
    icon: Search,
    title: "Stay current",
    text: "Ask about recent topics and AgentCoolie can bring current source links into the answer.",
  },
  {
    icon: Brain,
    title: "Keep context",
    text: "Important details about you, your goals, and your ongoing work can help later conversations.",
  },
  {
    icon: CalendarClock,
    title: "Act later",
    text: "Turn a message into a timed reminder or action task so the app can help when it matters.",
  },
];

export default function About() {
  return (
    <div className="h-full overflow-auto app-surface page-enter">
      <section className="relative overflow-hidden border-b">
        <div className="absolute inset-0 bg-grid-pattern opacity-[.06]" />
        <div className="relative mx-auto grid max-w-6xl gap-8 px-6 py-14 lg:grid-cols-[.95fr_1.05fr] lg:items-center">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
              <Bot className="h-4 w-4" />
              About AgentCoolie
            </div>
            <h1 className="max-w-4xl text-5xl font-bold leading-tight">
              A personal AI agent for context, current answers, and timely action.
            </h1>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-muted-foreground">
              AgentCoolie helps when your work depends on memory, fresh information, attachments, and follow-ups. It is designed to reduce repeated explanation and keep your next action close.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/chat">
                <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                  <MessageSquare className="h-4 w-4" />
                  Try Chat
                </Button>
              </Link>
              <Link href="/tasks">
                <Button variant="outline" className="gap-2 hover:border-primary/50 hover:text-primary">
                  <CalendarClock className="h-4 w-4" />
                  View Tasks
                </Button>
              </Link>
            </div>
          </div>

          <div className="rounded-lg border bg-[#11141b] p-5 text-white shadow-xl">
            <div className="mb-4 flex items-center gap-3">
              <div className="agent-mark flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
                <Bot className="relative z-10 h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <p className="font-semibold">Useful in everyday work</p>
                <p className="text-sm text-white/60">Memory, search, files, reminders</p>
              </div>
            </div>
            <div className="grid gap-3">
              {[
                { icon: Brain, text: "Remember that I am preparing for IAS" },
                { icon: Search, text: "Find recent Tamil Nadu politics news" },
                { icon: FileText, text: "Explain this attached screenshot" },
                { icon: Bell, text: "Remind me tomorrow morning" },
              ].map((item) => (
                <div key={item.text} className="landing-chat-line flex items-center gap-3 rounded-lg bg-white/10 p-3">
                  <item.icon className="h-5 w-5 text-primary" />
                  <span className="text-sm text-white/86">{item.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-10 md:grid-cols-2">
        {pillars.map((pillar) => (
          <article key={pillar.title} className="rounded-lg border bg-card p-6 hover-lift">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <pillar.icon className="h-6 w-6" />
            </div>
            <h2 className="mb-2 text-xl font-semibold">{pillar.title}</h2>
            <p className="leading-7 text-muted-foreground">{pillar.text}</p>
          </article>
        ))}
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-12">
        <div className="overflow-hidden rounded-lg border bg-card">
          <div className="grid lg:grid-cols-[.9fr_1.1fr]">
            <div className="bg-[#11141b] p-6 text-white">
              <div className="grid h-full min-h-[360px] content-center gap-3 rounded-lg border border-white/12 bg-white/8 p-5">
                {["Context saved", "Current source found", "Reminder scheduled", "Next step suggested"].map((item, index) => (
                  <div key={item} className="flex items-center gap-3 rounded-lg bg-white/10 p-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/20 text-xs text-primary">
                      {index + 1}
                    </div>
                    <span className="text-sm text-white/86">{item}</span>
                    <CheckCircle2 className="ml-auto h-5 w-5 text-primary" />
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-6 p-8">
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm text-primary">
                <Sparkles className="h-4 w-4" />
                How it helps
              </div>
              <h2 className="text-3xl font-bold">AgentCoolie connects your question to what it already knows and what needs to happen next.</h2>
              <p className="leading-7 text-muted-foreground">
                Use it for study planning, current affairs, attachments, reminders, websites, and repeated daily tasks. The app is most useful when you want one place that remembers context and helps you act.
              </p>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border p-4">
                  <Globe className="mb-3 h-6 w-6 text-primary" />
                  <p className="text-sm font-semibold">Current answers</p>
                </div>
                <div className="rounded-lg border p-4">
                  <Bell className="mb-3 h-6 w-6 text-primary" />
                  <p className="text-sm font-semibold">Timed actions</p>
                </div>
                <div className="rounded-lg border p-4">
                  <Brain className="mb-3 h-6 w-6 text-primary" />
                  <p className="text-sm font-semibold">Remembered context</p>
                </div>
              </div>
              <Link href="/chat">
                <Button variant="outline" className="hover:border-primary/50 hover:text-primary">
                  Ask AgentCoolie
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
