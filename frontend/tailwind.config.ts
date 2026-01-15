import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Background colors (Dark theme primary)
        background: {
          DEFAULT: "hsl(var(--background))",
          primary: "#0A0A0F",
          secondary: "#12121A",
          tertiary: "#1A1A24",
          elevated: "#22222E",
        },
        foreground: "hsl(var(--foreground))",
        
        // Text colors
        text: {
          primary: "#FAFAFA",
          secondary: "#A1A1AA",
          muted: "#71717A",
        },
        
        // Accent colors
        accent: {
          DEFAULT: "hsl(var(--accent))",
          primary: "#6366F1",
          hover: "#818CF8",
          glow: "rgba(99, 102, 241, 0.12)",
          foreground: "hsl(var(--accent-foreground))",
        },
        
        // Status colors
        status: {
          success: "#22C55E",
          "success-bg": "rgba(34, 197, 94, 0.08)",
          failed: "#EF4444",
          "failed-bg": "rgba(239, 68, 68, 0.08)",
          pending: "#F59E0B",
          "pending-bg": "rgba(245, 158, 11, 0.08)",
          info: "#3B82F6",
        },
        
        // Border colors
        border: {
          DEFAULT: "hsl(var(--border))",
          primary: "#27272A",
          hover: "#3F3F46",
        },
        
        // shadcn/ui compatibility
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        ring: "hsl(var(--ring))",
        input: "hsl(var(--input))",
        chart: {
          "1": "hsl(var(--chart-1))",
          "2": "hsl(var(--chart-2))",
          "3": "hsl(var(--chart-3))",
          "4": "hsl(var(--chart-4))",
          "5": "hsl(var(--chart-5))",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "display": ["32px", { lineHeight: "1.2", fontWeight: "700", letterSpacing: "-0.02em" }],
        "heading": ["24px", { lineHeight: "1.3", fontWeight: "600", letterSpacing: "-0.01em" }],
        "title": ["18px", { lineHeight: "1.4", fontWeight: "600" }],
        "subtitle": ["16px", { lineHeight: "1.5", fontWeight: "500" }],
        "body": ["14px", { lineHeight: "1.5", fontWeight: "400" }],
        "body-sm": ["13px", { lineHeight: "1.5", fontWeight: "400" }],
        "caption": ["12px", { lineHeight: "1.4", fontWeight: "400", letterSpacing: "0.02em" }],
      },
      spacing: {
        "xs": "4px",
        "sm": "8px",
        "md": "12px",
        "lg": "24px",
        "xl": "32px",
        "2xl": "48px",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        "sm": "0 1px 2px rgba(0, 0, 0, 0.3)",
        "md": "0 4px 6px rgba(0, 0, 0, 0.3)",
        "lg": "0 10px 15px rgba(0, 0, 0, 0.4)",
        "glow": "0 0 20px var(--accent-glow)",
        "card": "0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.24)",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-in": "slideIn 0.2s ease-out",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "count-up": "countUp 0.5s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        countUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
