import { useEffect, useState } from "react";
import { Link } from "wouter";
import {
  ArrowRight,
  Bell,
  Bot,
  Brain,
  CalendarClock,
  CheckCircle2,
  CheckSquare,
  FileText,
  Globe,
  MessageSquare,
  Search,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  type CarouselApi,
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

const slides = [
  {
    title: "Ask once, continue with context",
    description:
      "AgentCoolie can remember useful facts like your college, goals, preferences, and recent conversation so follow-up questions feel natural.",
    href: "/chat",
    cta: "Continue Chat",
    icon: Brain,
    visual: "memory",
  },
  {
    title: "Get current answers with sources",
    description:
      "Ask for recent news, current affairs, or fresh web information and get a useful answer with source links.",
    href: "/chat",
    cta: "Ask Current News",
    icon: Search,
    visual: "search",
  },
  {
    title: "Schedule reminders and actions",
    description:
      "Create tasks like opening a song later, reviewing a topic tomorrow, or reminding yourself before a deadline.",
    href: "/tasks",
    cta: "Create Task",
    icon: CalendarClock,
    visual: "tasks",
  },
];

const quickActions = [
  {
    title: "Start Chat",
    description: "Ask questions, upload files, or continue a remembered conversation.",
    icon: MessageSquare,
    href: "/chat",
  },
  {
    title: "Search Web",
    description: "Ask for recent links and summaries without leaving the chat.",
    icon: Search,
    href: "/chat",
  },
  {
    title: "Tasks",
    description: "Create reminders and action tasks with due times.",
    icon: CheckSquare,
    href: "/tasks",
  },
  {
    title: "Open Websites",
    description: "Ask AgentCoolie to open or inspect a website for you.",
    icon: Globe,
    href: "/website",
  },
];

const strengths = [
  { icon: Zap, label: "Less friction", text: "Ask naturally instead of switching between tools and tabs." },
  { icon: Shield, label: "Your workspace", text: "Your conversations, tasks, and reminders stay tied to your account." },
  { icon: Brain, label: "Context-aware", text: "The assistant can use remembered facts when they are useful." },
];

function SlideVisual({ type }: { type: string }) {
  if (type === "search") {
    return (
      <div className="grid h-full gap-3 p-5 text-white">
        <div className="rounded-lg border border-white/12 bg-white/10 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm text-white/72">
            <Search className="h-4 w-4 text-primary" />
            Current search
          </div>
          <p className="text-lg font-semibold">recent Tamil Nadu politics news</p>
        </div>
        {["The Hindu", "NDTV", "BBC"].map((source, index) => (
          <div key={source} className="landing-chat-line flex items-center gap-3 rounded-lg bg-white/10 p-3" style={{ animationDelay: `${index * 220}ms` }}>
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/20 text-xs text-primary">{index + 1}</div>
            <div>
              <p className="text-sm font-semibold">{source} result found</p>
              <p className="text-xs text-white/58">Fresh source ready for summary</p>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (type === "tasks") {
    return (
      <div className="grid h-full gap-3 p-5 text-white">
        {[
          { icon: Bell, title: "Review current affairs", time: "Tomorrow, 8:00 AM" },
          { icon: Globe, title: "Open Amazon", time: "When requested" },
          { icon: CalendarClock, title: "Play study playlist", time: "7:00 PM" },
        ].map((task, index) => (
          <div key={task.title} className="landing-chat-line flex items-center gap-3 rounded-lg border border-white/12 bg-white/10 p-4" style={{ animationDelay: `${index * 260}ms` }}>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <task.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold">{task.title}</p>
              <p className="text-sm text-white/62">{task.time}</p>
            </div>
            <CheckCircle2 className="ml-auto h-5 w-5 text-primary" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid h-full gap-3 p-5 text-white">
      <div className="rounded-lg border border-white/12 bg-white/10 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm text-white/72">
          <Brain className="h-4 w-4 text-primary" />
          Remembered for Sai
        </div>
        <div className="flex flex-wrap gap-2">
          {["KMIT college", "IAS preparation", "Maths score: 89", "Tamil Nadu politics"].map((chip) => (
            <span key={chip} className="rounded-md bg-white/12 px-3 py-1.5 text-sm">{chip}</span>
          ))}
        </div>
      </div>
      <div className="landing-chat-line ml-auto max-w-[88%] rounded-lg bg-primary p-4 text-primary-foreground">
        <p className="text-sm text-white/68">You ask</p>
        <p className="font-semibold">What should I revise today?</p>
      </div>
      <div className="landing-chat-line landing-delay-1 max-w-[92%] rounded-lg bg-white/10 p-4">
        <p className="text-sm text-white/68">AgentCoolie replies</p>
        <p className="font-semibold">Let us connect it to your IAS prep and recent marks.</p>
      </div>
    </div>
  );
}

export default function Home() {
  const { user } = useAuth();
  const [api, setApi] = useState<CarouselApi>();
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    if (!api) return;
    const onSelect = () => setSelected(api.selectedScrollSnap());
    onSelect();
    api.on("select", onSelect);
    return () => {
      api.off("select", onSelect);
    };
  }, [api]);

  useEffect(() => {
    if (!api) return;
    let timer: number | undefined;

    const stopAutoAdvance = () => {
      if (timer !== undefined) {
        window.clearInterval(timer);
        timer = undefined;
      }
    };

    const startAutoAdvance = () => {
      stopAutoAdvance();
      if (document.hidden) return;
      timer = window.setInterval(() => api.scrollNext(), 7000);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopAutoAdvance();
      } else {
        startAutoAdvance();
      }
    };

    startAutoAdvance();
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopAutoAdvance();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [api]);

  return (
    <div className="h-full overflow-auto app-surface page-enter">
      <section className="relative overflow-hidden border-b">
        <div className="absolute inset-0 bg-grid-pattern opacity-[.06]" />
        <div className="relative mx-auto grid max-w-7xl gap-8 px-6 py-10 lg:grid-cols-[1.05fr_.95fr] lg:items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
              <Bot className="h-4 w-4" />
              Personal AI Agent
            </div>

            <div className="space-y-4">
              <h1 className="max-w-3xl text-5xl font-bold leading-tight md:text-6xl" data-testid="text-greeting">
                Welcome back, {user?.displayName?.split(" ")[0] || "there"}.
                <span className="block text-primary">Let AgentCoolie keep the context.</span>
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
                Chat naturally, ask for current information, attach files, and schedule tasks without repeating your background every time.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href="/chat">
                <Button size="lg" className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                  <MessageSquare className="h-4 w-4" />
                  Start Asking
                </Button>
              </Link>
              <Link href="/tasks">
                <Button size="lg" variant="outline" className="gap-2 hover:border-primary/50 hover:text-primary">
                  Create a Task
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>

          <Carousel setApi={setApi} opts={{ align: "start", loop: true }} className="min-w-0">
            <CarouselContent>
              {slides.map((slide) => (
                <CarouselItem key={slide.title}>
                  <div className="group overflow-hidden rounded-lg border bg-[#10131a] shadow-xl">
                    <div className="relative grid min-h-[430px] overflow-hidden lg:grid-cols-[.9fr_1.1fr]">
                      <div className="space-y-4 p-6 text-white">
                        <div className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-primary shadow-lg shadow-primary/30">
                          <slide.icon className="h-5 w-5" />
                        </div>
                        <h2 className="text-3xl font-semibold leading-tight text-white">{slide.title}</h2>
                        <p className="max-w-md text-sm leading-6 text-white/82">{slide.description}</p>
                        <Link href={slide.href}>
                          <Button className="bg-white text-slate-950 hover:bg-white/90">{slide.cta}</Button>
                        </Link>
                      </div>
                      <div className="relative border-t border-white/10 bg-white/5 lg:border-l lg:border-t-0">
                        <SlideVisual type={slide.visual} />
                      </div>
                      <div key={selected} className="absolute inset-x-0 bottom-0 h-1 bg-white/20">
                        <div className="h-full w-full bg-primary slide-progress" />
                      </div>
                    </div>
                  </div>
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious className="left-3 border-white/30 bg-black/30 text-white hover:bg-black/50" />
            <CarouselNext className="right-3 border-white/30 bg-black/30 text-white hover:bg-black/50" />
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {slides.map((slide, index) => (
                <button
                  key={slide.title}
                  type="button"
                  onClick={() => api?.scrollTo(index)}
                  className={cn(
                    "pressable rounded-lg border bg-card p-3 text-left shadow-sm",
                    selected === index ? "border-primary bg-primary/5" : "hover:border-primary/40",
                  )}
                >
                  <div className="mb-2 flex items-center gap-2">
                    <slide.icon className={cn("h-4 w-4", selected === index ? "text-primary" : "text-muted-foreground")} />
                    <span className="text-xs font-medium text-muted-foreground">Use case {index + 1}</span>
                  </div>
                  <p className="text-sm font-semibold leading-5">{slide.title}</p>
                </button>
              ))}
            </div>
          </Carousel>
        </div>
      </section>

      <section className="mx-auto max-w-7xl space-y-10 px-6 py-10">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {quickActions.map((action) => (
            <Link key={action.title} href={action.href}>
              <Card className="group h-full p-5 interactive-card pressable">
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <action.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-lg font-semibold group-hover:text-primary">{action.title}</h3>
                <p className="text-sm leading-6 text-muted-foreground">{action.description}</p>
              </Card>
            </Link>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-[.9fr_1.1fr] lg:items-stretch">
          <div className="rounded-lg border bg-card p-7 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <div className="agent-mark flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
                <Bot className="relative z-10 h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-primary">About AgentCoolie</p>
                <h2 className="text-2xl font-bold">A helper that remembers what you should not have to repeat.</h2>
              </div>
            </div>
            <p className="leading-7 text-muted-foreground">
              AgentCoolie is useful when your question depends on who you are, what you are working toward, what just happened, or what needs to happen later.
            </p>
            <div className="mt-6">
              <Link href="/about">
                <Button variant="outline" className="gap-2 hover:border-primary/50 hover:text-primary">
                  Open About Page
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {strengths.map((item) => (
              <div key={item.label} className="rounded-lg border bg-card p-5 pressable">
                <item.icon className="mb-4 h-8 w-8 text-primary" />
                <h3 className="mb-2 font-semibold">{item.label}</h3>
                <p className="text-sm leading-6 text-muted-foreground">{item.text}</p>
              </div>
            ))}
          </div>
        </div>

        <section className="overflow-hidden rounded-lg border bg-card">
          <div className="grid lg:grid-cols-[1fr_.8fr]">
            <div className="space-y-5 p-8">
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm text-primary">
                <Sparkles className="h-4 w-4" />
                Designed for daily use
              </div>
              <h2 className="text-3xl font-bold">Use it for studying, current affairs, files, reminders, and web actions.</h2>
              <p className="leading-7 text-muted-foreground">
                AgentCoolie is built for practical requests: remember this, explain this image, find recent updates, open that site, remind me later, or help me plan what to do next.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link href="/tasks">
                  <Button className="bg-primary text-primary-foreground hover:bg-primary/90">Create a Task</Button>
                </Link>
                <Link href="/chat">
                  <Button variant="outline">Ask AgentCoolie</Button>
                </Link>
              </div>
            </div>
            <div className="bg-[#11141b] p-6 text-white">
              <div className="grid h-full min-h-[320px] content-center gap-3 rounded-lg border border-white/12 bg-white/8 p-5">
                {[
                  { icon: FileText, text: "Summarize a PDF or screenshot" },
                  { icon: Search, text: "Find recent news with sources" },
                  { icon: Bell, text: "Remind me before a deadline" },
                  { icon: Globe, text: "Open a useful website" },
                ].map((item) => (
                  <div key={item.text} className="flex items-center gap-3 rounded-lg bg-white/10 p-3">
                    <item.icon className="h-5 w-5 text-primary" />
                    <span className="text-sm text-white/86">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </section>
    </div>
  );
}
