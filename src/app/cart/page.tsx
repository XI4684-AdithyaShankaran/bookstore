import { ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function CartPage() {
    return (
        <div className="container mx-auto px-4 py-12 text-center">
            <ShoppingCart className="mx-auto h-24 w-24 text-muted-foreground/50" />
            <h1 className="text-4xl font-bold mt-8 font-headline">Your Cart is Empty</h1>
            <p className="mt-4 text-lg text-muted-foreground">
                Looks like you haven't added any books to your cart yet.
            </p>
            <Button asChild className="mt-8">
                <Link href="/">Start Browsing</Link>
            </Button>
        </div>
    );
}
