"use client";

import { Moon, Sun } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useLocale } from "@/hooks/use-locale";
import { useTheme } from "@/hooks/use-theme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const { t } = useLocale();

  function handleToggle() {
    toggleTheme();
    const next = theme === "dark" ? "light" : "dark";
    toast.success(
      next === "dark" ? t("toast.themeDark") : t("toast.themeLight"),
    );
  }

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={handleToggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </Button>
  );
}
