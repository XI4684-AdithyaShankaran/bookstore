'use client';

import Link from 'next/link';
import { BookMarked, Heart, Menu, Search, ShoppingCart, User } from 'lucide-react';
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

const NavLinks = ({ inSheet = false, onLinkClick }: { inSheet?: boolean; onLinkClick?: () => void }) => (
  <nav
    className={
      inSheet
        ? 'flex flex-col space-y-4 text-lg'
        : 'hidden md:flex items-center space-x-1'
    }
  >
     <Button variant="ghost" asChild>
      <Link href="/recommendations" onClick={onLinkClick}>
        Discover
      </Link>
    </Button>
    <Button variant="ghost" asChild>
      <Link href="/bookshelves" onClick={onLinkClick}>
        Bookshelves
      </Link>
    </Button>
  </nav>
);

export default function Header() {
  const isMobile = useIsMobile();
  const [sheetOpen, setSheetOpen] = useState(false);
  const closeSheet = () => setSheetOpen(false);

  return (
    <header className="bg-background/80 backdrop-blur-sm border-b sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link
            href="/"
            className="text-2xl font-bold text-primary font-headline"
          >
            bkmrk'd
          </Link>

          <div className="hidden md:flex flex-1 justify-center px-8">
             <NavLinks />
          </div>

          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className='hidden md:inline-flex'>
                <Search />
                <span className="sr-only">Search</span>
            </Button>
             <Button variant="ghost" size="icon" asChild>
              <Link href="/wishlist">
                <Heart />
                <span className="sr-only">Wishlist</span>
              </Link>
            </Button>
             <Button variant="ghost" size="icon" asChild>
              <Link href="/cart">
                <ShoppingCart />
                <span className="sr-only">Cart</span>
              </Link>
            </Button>
             <Button variant="ghost" size="icon" asChild>
              <Link href="/bookshelves">
                <BookMarked />
                <span className="sr-only">Bookshelves</span>
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
                    <NavLinks inSheet onLinkClick={closeSheet} />
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
