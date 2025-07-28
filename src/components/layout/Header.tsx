'use client';

import Link from 'next/link';
import { BookOpen, Sparkles, User, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { useIsMobile } from '@/hooks/use-mobile';
import { useState } from 'react';

const NavLinks = ({ inSheet = false }: { inSheet?: boolean }) => (
  <nav
    className={
      inSheet
        ? 'flex flex-col space-y-4 text-lg'
        : 'hidden md:flex items-center space-x-6'
    }
  >
    <Link
      href="/recommendations"
      className="flex items-center gap-2 hover:text-primary transition-colors"
    >
      <Sparkles className="w-4 h-4" />
      AI Recommendations
    </Link>
    <Link
      href="/bookshelves"
      className="flex items-center gap-2 hover:text-primary transition-colors"
    >
      <BookOpen className="w-4 h-4" />
      My Bookshelves
    </Link>
  </nav>
);

export default function Header() {
  const isMobile = useIsMobile();
  const [sheetOpen, setSheetOpen] = useState(false);

  return (
    <header className="bg-card/80 backdrop-blur-lg border-b sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link
            href="/"
            className="text-2xl font-bold text-primary font-headline"
          >
            BibliophileAI
          </Link>

          <NavLinks />

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/login">
                <User />
                <span className="sr-only">Profile</span>
              </Link>
            </Button>
            {isMobile && (
              <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Menu />
                    <span className="sr-only">Open menu</span>
                  </Button>
                </SheetTrigger>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>BibliophileAI</SheetTitle>
                  </SheetHeader>
                  <div className="py-8">
                    <NavLinks inSheet />
                  </div>
                </SheetContent>
              </Sheet>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
