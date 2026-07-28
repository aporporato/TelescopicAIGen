import { Injectable } from '@angular/core';
import { GoogleGenAI, Type } from '@google/genai';

export interface StorySegment {
  content: string;
  expandable: boolean;
}

export function parseReplacement(text: string): StorySegment[] {
  const regex = /\[\[(.*?)\]\]|(\S+)/g;
  let match;
  const result: StorySegment[] = [];
  
  while ((match = regex.exec(text)) !== null) {
    if (match[1] !== undefined) {
      result.push({
        content: match[1],
        expandable: true
      });
    } else if (match[2] !== undefined) {
      result.push({
        content: match[2],
        expandable: false
      });
    }
  }
  return result;
}

@Injectable({ providedIn: 'root' })
export class TelescopicService {
  private ai: GoogleGenAI;

  constructor() {
    const apiKey = (window as any).process?.env?.API_KEY ?? '';
    this.ai = new GoogleGenAI({ apiKey });
  }

  private readonly responseSchema = {
    type: Type.ARRAY,
    items: {
      type: Type.OBJECT,
      properties: {
        content: {
          type: Type.STRING,
          description: 'A segment of the story text.',
        },
        expandable: {
          type: Type.BOOLEAN,
          description: 'Whether this segment can be expanded further.',
        },
      },
      required: ['content', 'expandable'],
    },
  };

  async generateInitialStory(prompt: string): Promise<StorySegment[]> {
    const systemInstruction = `You are a creative writer. Your task is to start a story based on a user's prompt. 
    1. Write a single, compelling opening sentence.
    2. Break down this sentence into segments of text.
    3. Identify 2-4 interesting nouns or verb phrases within the sentence that could be expanded upon to continue the story. Mark these as expandable.
    4. Return the result as a JSON array of objects, each with 'content' and 'expandable' properties, according to the provided schema.
    5. Ensure the segments, when joined, form the complete, original sentence. Non-expandable text segments should surround the expandable ones.`;

    const response = await this.ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `Prompt: "${prompt}"`,
      config: {
        systemInstruction,
        responseMimeType: 'application/json',
        responseSchema: this.responseSchema,
        temperature: 0.8,
      },
    });
    
    const jsonText = response.text.trim();
    return JSON.parse(jsonText) as StorySegment[];
  }

  async expandText(
    contextOrBlank: string, 
    textToExpand?: string,
    provider?: string,
    model?: string,
    apiKey?: string
  ): Promise<StorySegment[]> {
    // If backend provider and apiKey are supplied with a blank sentence, call backend /api/expand
    if (provider && apiKey && contextOrBlank.includes('_')) {
      const res = await fetch('/api/expand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sentence_with_blank: contextOrBlank,
          provider: provider,
          model: model || 'gpt-5.4-nano',
          api_key: apiKey
        })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'AI expansion failed');
      }
      const data = await res.json();
      return parseReplacement(data.replacement || '');
    }

    const systemInstruction = `You are a master of unfolding narratives, continuing a story by elaborating on a specific phrase.
    1. You will be given the story so far (context) and a specific phrase to expand.
    2. Write one or two concise sentences that elaborate ONLY on the given phrase, seamlessly continuing the narrative.
    3. Break down your new sentences into segments, identifying 1-3 new interesting words or phrases to be expandable.
    4. Return your elaboration as a JSON array of objects, following the provided schema.
    5. Do NOT repeat the phrase to expand in your response. Your response is what comes AFTER it.
    6. Your response should start with a space to properly connect to the preceding word.`;
    
    const contents = `Context: "${contextOrBlank}"\n\nPhrase to expand: "${textToExpand || ''}"`;

    const response = await this.ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents,
      config: {
        systemInstruction,
        responseMimeType: 'application/json',
        responseSchema: this.responseSchema,
        temperature: 0.9,
      },
    });

    const jsonText = response.text.trim();
    return JSON.parse(jsonText) as StorySegment[];
  }
}
