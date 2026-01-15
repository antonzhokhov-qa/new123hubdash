"use client";

import { ReactNode, useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChartRowProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function ChartRow({ title, children, className }: ChartRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const scrollAmount = 420; // Slightly more than min-width of cards
    const currentScroll = scrollRef.current.scrollLeft;
    const newScroll = direction === "left" 
      ? currentScroll - scrollAmount 
      : currentScroll + scrollAmount;
    
    scrollRef.current.scrollTo({
      left: newScroll,
      behavior: "smooth",
    });
  };

  return (
    <div className={cn("relative group", className)}>
      {title && (
        <h3 className="text-sm font-medium text-text-muted mb-3 px-1">
          {title}
        </h3>
      )}
      
      {/* Scroll buttons */}
      <Button
        variant="outline"
        size="icon"
        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 h-8 w-8 rounded-full bg-background-primary/90 backdrop-blur border-border-primary shadow-lg opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-0"
        onClick={() => scroll("left")}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      
      <Button
        variant="outline"
        size="icon"
        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 h-8 w-8 rounded-full bg-background-primary/90 backdrop-blur border-border-primary shadow-lg opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-0"
        onClick={() => scroll("right")}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>

      {/* Gradient overlays for scroll indication */}
      <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-background-primary to-transparent pointer-events-none z-[5] opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-background-primary to-transparent pointer-events-none z-[5] opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Scrollable container */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-thin scrollbar-thumb-border-primary scrollbar-track-transparent"
        style={{
          scrollbarWidth: "thin",
          msOverflowStyle: "none",
        }}
      >
        {children}
      </div>

      {/* Custom scrollbar styles */}
      <style jsx>{`
        div::-webkit-scrollbar {
          height: 6px;
        }
        div::-webkit-scrollbar-track {
          background: transparent;
        }
        div::-webkit-scrollbar-thumb {
          background: var(--border-primary);
          border-radius: 3px;
        }
        div::-webkit-scrollbar-thumb:hover {
          background: var(--text-muted);
        }
      `}</style>
    </div>
  );
}

// Wrapper for individual chart cards in row to add snap behavior
interface ChartRowItemProps {
  children: ReactNode;
  className?: string;
}

export function ChartRowItem({ children, className }: ChartRowItemProps) {
  return (
    <div className={cn("snap-start flex-shrink-0", className)}>
      {children}
    </div>
  );
}
