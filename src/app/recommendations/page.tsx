import RecommendationForm from '@/components/recommendations/RecommendationForm';
import { Sparkles } from 'lucide-react';

export default function RecommendationsPage() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-2xl mx-auto text-center">
        <Sparkles className="mx-auto h-12 w-12 text-accent" />
        <h1 className="text-4xl font-bold mt-4 font-headline">
          AI Book Recommender
        </h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Describe the kind of book you're looking for, and our AI will find
          the perfect match for you.
        </p>
      </div>

      <div className="max-w-2xl mx-auto mt-8">
        <RecommendationForm />
      </div>
    </div>
  );
}
