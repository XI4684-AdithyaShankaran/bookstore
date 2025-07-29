# **App Name**: BibliophileAI

## Core Features:

- Infinite Scroll Grid: Displays books in an infinite-scrolling grid format, similar to Pinterest, using React for the frontend.
- Book Detail View: Show detailed information about each book including title, author, description, and associated metadata.
- Book Actions (Cart, Wishlist, Bookshelf): Users can add books to their personalized cart, wishlist, or create custom bookshelves.
- AI Book Recommendation Engine: A tool leveraging generative AI to provide book recommendations based on user-created bookshelves, and also suggests similar books based on viewed details. The AI tool will use reasoning to decide when or if to incorporate some piece of information in its output. The AI uses agentic ai, mcp server, langchain, prompting, Gemini configurations, temperature settings, and a vector db.
- Custom Bookshelves: Users can create and manage multiple bookshelves with custom names and descriptions to categorize their books.
- User Authentication with JWT and oauth: Uses FastAPI in the backend to handle authentication and authorization using JWT and oauth for user registration.
- Kaggle Book Data Persistence: Integrates with a PostgreSQL database to store book details and the user account details. Fetches data from Kaggle. Redis and Celery might be used for caching and asynchronous tasks. Tech stack includes: Python, Postgres, Weaviate (vector db), LangGraph, nginx/gce

## Style Guidelines:

- Primary color: HSL(210, 60%, 50%) / Hex:#478CCA - A professional and trustworthy blue, to reflect credibility and safety.
- Background color: HSL(210, 20%, 95%) / Hex: #F0F4F7 - a desaturated, very light tint of the primary blue as a clean, calming backdrop for content.
- Accent color: HSL(30, 90%, 50%) / Hex:#F2A63F - a warm, inviting gold hue. A different brightness and saturation provide contrast for calls to action and highlights, drawing users' attention without overwhelming the UI.
- Body and headline font: 'Inter', a grotesque-style sans-serif with a modern, machined, objective, neutral look; suitable for headlines or body text.
- Use clear, consistent icons from a library like FontAwesome or Material Design to represent book genres, actions (add to cart, wishlist), and bookshelf management.
- Pinterest-style grid layout with responsive design to adapt to different screen sizes, with clearly defined sections for login/signup, book browsing, bookshelves, and recommendations.
- Subtle animations on book hover, loading states, and transitions between views to provide feedback and enhance user experience.