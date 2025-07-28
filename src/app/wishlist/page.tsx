import { Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function WishlistPage() {
    return (
        <div className="container mx-auto px-4 py-12 text-center">
            <Heart className="mx-auto h-24 w-24 text-muted-foreground/50" />
            <h1 className="text-4xl font-bold mt-8 font-headline">Your Wishlist is Empty</h1>
            <p className="mt-4 text-lg text-muted-foreground">
                Add books to your wishlist to save them for later.
            </p>
            <Button asChild className="mt-8">
                <Link href="/">Discover Books</Link>
            </Button>
        </div>
    );
}
