'use client';

import Link from 'next/link';
import { BookOpen, User, Menu, Search, Bell } from 'lucide-react';
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
import { Input } from '../ui/input';

const NavLinks = ({ inSheet = false }: { inSheet?: boolean }) => (
  <nav
    className={
      inSheet
        ? 'flex flex-col space-y-4 text-lg'
        : 'hidden md:flex items-center space-x-6'
    }
  >
    <Button variant="ghost" asChild>
      <Link
        href="#"
      >
        Journal Page
      </Link>
    </Button>
  </nav>
);

export default function Header() {
  const isMobile = useIsMobile();
  const [sheetOpen, setSheetOpen] = useState(false);

  return (
    <header className="bg-background/80 backdrop-blur-lg border-b sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link
            href="/"
            className="text-2xl font-bold text-primary font-headline"
          >
            bkmrk'd
          </Link>

          <div className="flex-1 flex justify-center px-8">
             <div className="relative w-full max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input placeholder="Search" className="pl-10 bg-muted border-none" />
             </div>
          </div>


          <div className="flex items-center gap-2">
            <NavLinks />
            <Button variant="ghost" size="icon" asChild>
              <Link href="#">
                <Bell />
                <span className="sr-only">Notifications</span>
              </Link>
            </Button>
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
                    <SheetTitle>bkmrk'd</SheetTitle>
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
