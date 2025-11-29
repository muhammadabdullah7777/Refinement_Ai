# Firebase Frontend Tech Stack Documentation

## Overview

Your Next.js Firebase frontend technology stack for the AI Agent application, including integration with the enhanced AI API.

## Core Technology Stack

### Frontend Framework

- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **React 18** - UI library with hooks and concurrent features

### Firebase Services

- **Firebase Authentication** - User management and authentication
- **Firestore Database** - Real-time data storage
- **Firebase Hosting** - Production deployment
- **Firebase Storage** - File storage (if needed for uploads)
- **Firebase Functions** - Serverless backend (optional)

### UI & Styling

- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Reusable component library
- **React Hook Form** - Form management and validation
- **Zod** - Schema validation

### State Management

- **Zustand** or **Redux Toolkit** - Global state management
- **React Query (TanStack Query)** - Server state management
- **React Context** - Local state sharing

### Additional Libraries

- **Axios** or **Fetch API** - HTTP requests to AI API
- **date-fns** - Date manipulation
- **Lucide React** - Icon library
- **React Hot Toast** - Notifications

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── chat/
│   │   └── page.tsx       # Chat interface
│   └── api/               # API routes (if needed)
├── components/            # Reusable components
│   ├── ui/               # shadcn/ui components
│   ├── chat/
│   │   ├── ChatInterface.tsx
│   │   ├── MessageBubble.tsx
│   │   └── ModelToggle.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Sidebar.tsx
├── lib/                   # Utility libraries
│   ├── utils.ts
│   ├── api.ts            # AI API integration
│   └── firebase.ts       # Firebase configuration
├── hooks/                # Custom React hooks
│   ├── useChat.ts
│   ├── useAuth.ts
│   └── useStreaming.ts
├── store/                # State management
│   └── chatStore.ts
├── types/                # TypeScript definitions
│   ├── chat.ts
│   └── api.ts
└── public/               # Static assets
```

## AI API Integration

### Core API Client

```typescript
// lib/api.ts
import { ChatRequest, ChatResponse, ComparisonResponse } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export class AIClient {
  static async sendMessage(
    message: string,
    stream = false
  ): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        include_models: ["deepseek", "moonshot"],
        stream,
      } as ChatRequest),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  static async compareResponses(message: string): Promise<ComparisonResponse> {
    const response = await fetch(`${API_BASE_URL}/compare`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message } as ChatRequest),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  static async streamMessage(
    message: string,
    onChunk: (data: any) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          stream: true,
        } as ChatRequest),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              onChunk(data);
            } catch (e) {
              console.error("Parse error:", e);
            }
          }
        }
      }

      onComplete();
    } catch (error) {
      onError(error as Error);
    }
  }
}
```

### Custom React Hooks

#### useChat Hook

```typescript
// hooks/useChat.ts
import { useState, useCallback } from "react";
import { AIClient } from "@/lib/api";
import { useChatStore } from "@/store/chatStore";

export function useChat() {
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const { addMessage, updateMessage } = useChatStore();

  const sendMessage = useCallback(
    async (content: string, stream = false) => {
      setIsLoading(true);

      const userMessage = addMessage({
        content,
        role: "user",
        timestamp: new Date(),
      });

      try {
        if (stream) {
          setIsStreaming(true);
          await AIClient.streamMessage(
            content,
            (chunk) => {
              switch (chunk.type) {
                case "model_output":
                  updateMessage({
                    ...userMessage,
                    modelOutputs: {
                      ...userMessage.modelOutputs,
                      [chunk.data.model]: {
                        content: chunk.data.content,
                        status: chunk.data.status,
                      },
                    },
                  });
                  break;
                case "status":
                  // Update UI with processing status
                  break;
              }
            },
            () => {
              setIsStreaming(false);
              setIsLoading(false);
            },
            (error) => {
              console.error("Stream error:", error);
              setIsStreaming(false);
              setIsLoading(false);
            }
          );
        } else {
          const response = await AIClient.sendMessage(content);
          const aiMessage = addMessage({
            content: response.primary_response,
            role: "assistant",
            timestamp: new Date(),
            modelOutputs: response.model_outputs,
            metadata: {
              processing_time: response.total_processing_time,
            },
          });
          setIsLoading(false);
          return aiMessage;
        }
      } catch (error) {
        console.error("Chat error:", error);
        setIsLoading(false);
        setIsStreaming(false);
      }
    },
    [addMessage, updateMessage]
  );

  return {
    sendMessage,
    isLoading,
    isStreaming,
  };
}
```

#### useAuth Hook

```typescript
// hooks/useAuth.ts
import { useState, useEffect } from "react";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
} from "firebase/auth";
import { auth } from "@/lib/firebase";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    const result = await signInWithEmailAndPassword(auth, email, password);
    return result.user;
  };

  const signUp = async (email: string, password: string) => {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    return result.user;
  };

  const logout = () => signOut(auth);

  return {
    user,
    loading,
    signIn,
    signUp,
    logout,
  };
}
```

## Key Components

### Chat Interface Component

```typescript
// components/chat/ChatInterface.tsx
"use client";

import { useState } from "react";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ModelToggle } from "./ModelToggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ChatInterface() {
  const [message, setMessage] = useState("");
  const [selectedModel, setSelectedModel] = useState<
    "moonshot" | "deepseek" | "both"
  >("moonshot");
  const { sendMessage, isLoading, isStreaming } = useChat();
  const { messages } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    await sendMessage(message, true); // Enable streaming
    setMessage("");
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Header with model toggle */}
      <div className="p-4 border-b">
        <ModelToggle
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
        />
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} showModel={selectedModel} />
        ))}

        {(isLoading || isStreaming) && (
          <div className="flex justify-center">
            <div className="animate-pulse text-gray-500">
              {isStreaming ? "Streaming response..." : "Processing..."}
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading || isStreaming}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!message.trim() || isLoading || isStreaming}
          >
            Send
          </Button>
        </div>
      </form>
    </div>
  );
}
```

### Model Toggle Component

```typescript
// components/chat/ModelToggle.tsx
import { Button } from "@/components/ui/button";

interface ModelToggleProps {
  selectedModel: "moonshot" | "deepseek" | "both";
  onModelChange: (model: "moonshot" | "deepseek" | "both") => void;
}

export function ModelToggle({
  selectedModel,
  onModelChange,
}: ModelToggleProps) {
  return (
    <div className="flex gap-2">
      <Button
        variant={selectedModel === "moonshot" ? "default" : "outline"}
        onClick={() => onModelChange("moonshot")}
        size="sm"
      >
        Moonshot Only
      </Button>
      <Button
        variant={selectedModel === "deepseek" ? "default" : "outline"}
        onClick={() => onModelChange("deepseek")}
        size="sm"
      >
        DeepSeek Only
      </Button>
      <Button
        variant={selectedModel === "both" ? "default" : "outline"}
        onClick={() => onModelChange("both")}
        size="sm"
      >
        Compare Both
      </Button>
    </div>
  );
}
```

## Environment Configuration

```env
# .env.local
NEXT_PUBLIC_API_URL=https://your-ai-api-domain.com
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef123456
```

## Deployment Configuration

### Firebase Hosting

```json
// firebase.json
{
  "hosting": {
    "public": "out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**",
        "headers": [
          {
            "key": "X-Frame-Options",
            "value": "DENY"
          },
          {
            "key": "X-Content-Type-Options",
            "value": "nosniff"
          }
        ]
      }
    ]
  }
}
```

### Next.js Configuration

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
};

module.exports = nextConfig;
```

## Performance Optimization

### Code Splitting

- Use Next.js dynamic imports for heavy components
- Implement React.lazy for route-based splitting
- Optimize bundle size with tree shaking

### Caching Strategy

- Implement React Query for API response caching
- Use localStorage for user preferences
- Cache model comparisons for repeated queries

### Real-time Features

- WebSocket connections for live updates
- Firebase real-time listeners for collaborative features
- Optimistic updates for better UX

## Security Considerations

- Implement proper CORS policies
- Use Firebase Security Rules for database access
- Validate all API responses with Zod schemas
- Sanitize user inputs to prevent XSS
- Implement rate limiting on client-side

## Monitoring & Analytics

- Firebase Analytics for user behavior
- Custom event tracking for AI interactions
- Error monitoring with Firebase Crashlytics
- Performance monitoring with Web Vitals

This tech stack provides a solid foundation for building a scalable, performant AI chat application with excellent user experience and real-time capabilities.
