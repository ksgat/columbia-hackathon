Prophecy is a social prediction markets platform that gamifies forecasting and collective intelligence through AI-augmented wagering on
real-world events and hypothetical questions. Users create and join themed Rooms (customizable prediction spaces accessible via join codes)     
where they can propose prediction Markets covering binary yes/no questions, multiple-choice scenarios, or numeric predictions. Each
market operates on a Logarithmic Market Scoring Rule (LMSR) automated market maker that dynamically adjusts share prices based on trading       
activity, allowing users to buy and sell positions using their virtual token balance while the algorithm ensures market liquidity and calculates
real-time probabilities. 

The platform's unique feature is the Prophet, an AI agent powered by large language models that analyzes market         
questions to provide probability estimates with detailed reasoning, suggests relevant new markets based on room context and existing questions,
and helps users evaluate the quality of predictions before committing tokens. When markets close,
participants engage in a democratic resolution process by casting weighted votes on the true outcome (with voting power influenced by stake and
reputation), after which winning positions are paid out and user accuracy scores are updated.

Prophecy is built as a full-stack social prediction market platform leveraging a modern, production-ready technology stack. The backend is      
powered by FastAPI (Python's high-performance async web framework) running on Uvicorn with PostgreSQL as the primary database
accessed through Supabase. The AI-powered "Prophet" agent leverages OpenAI-compatible APIs through OpenRouter for generating market
predictions and analysis. 

The frontend is built with Next.js 14 and TypeScript, utilizing React 18 for the UI layer, Tailwind CSS for
styling, and Zustand for lightweight state management. Additionally, Supabase manages real-time subscriptions and database queries to enhance UX. The UI is enhanced with Framer Motion for smooth animations, Recharts for data visualization, Radix UI components for accessible primitives, and Lucide React for iconography, with Axios
handling HTTP requests to the backend API.
