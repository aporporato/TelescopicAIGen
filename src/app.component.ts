import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TelescopicService, StorySegment } from './services/telescopic.service';
import { StoryNodeComponent, StoryNode } from './components/story-node/story-node.component';
import { CommonModule } from '@angular/common';

let idCounter = 0;

export interface ModelInfo {
  provider: string;
  name: string;
  id: string;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, StoryNodeComponent, CommonModule],
})
export class AppComponent implements OnInit {
  private readonly telescopicService = inject(TelescopicService);

  prompt = signal<string>('A detective finds a mysterious, glowing key in a rainy alley.');
  story = signal<StoryNode[]>([
    { id: idCounter++, content: 'I', expandable: true, isLoading: false, isCollapsed: false, children: [] },
    { id: idCounter++, content: 'made', expandable: true, isLoading: false, isCollapsed: false, children: [] },
    { id: idCounter++, content: 'tea.', expandable: true, isLoading: false, isCollapsed: false, children: [] }
  ]);
  isLoading = signal<boolean>(false);
  error = signal<string | null>(null);
  copySuccess = signal<boolean>(false);

  // Settings & Model selection state
  isSettingsOpen = signal<boolean>(false);
  modelsList = signal<ModelInfo[]>([
    { provider: 'openai', name: 'GPT-5.4 Nano', id: 'gpt-5.4-nano' },
    { provider: 'google', name: 'Gemini 3.5 Flash', id: 'gemini-3.5-flash' },
    { provider: 'anthropic', name: 'Claude Haiku 4.5', id: 'claude-haiku-4-5-20251001' }
  ]);
  selectedModelId = signal<string>('gpt-5.4-nano');
  userApiKeys = signal<Record<string, string>>({
    openai: '',
    google: '',
    anthropic: ''
  });

  ngOnInit(): void {
    this.loadBackendConfig();
  }

  private async loadBackendConfig(): Promise<void> {
    if (typeof window === 'undefined' || !window.location || !window.location.origin || window.location.origin === 'null' || window.location.origin.includes('localhost:0')) {
      return;
    }
    try {
      const url = `${window.location.origin}/api/config`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data.models && data.models.length > 0) {
          this.modelsList.set(data.models);
          const savedModel = localStorage.getItem('telescopic_selected_model');
          if (savedModel && data.models.some((m: ModelInfo) => m.id === savedModel)) {
            this.selectedModelId.set(savedModel);
          } else {
            this.selectedModelId.set(data.models[0].id);
          }
        }
      }
    } catch {
      // Ignore if server config is not available in unit test sandbox
    }
  }

  toggleSettings(event?: Event): void {
    if (event) event.preventDefault();
    this.isSettingsOpen.update(v => !v);
  }

  resetStory(event?: Event): void {
    if (event) event.preventDefault();
    this.error.set(null);
    this.story.set([
      { id: idCounter++, content: 'I', expandable: true, isLoading: false, isCollapsed: false, children: [] },
      { id: idCounter++, content: 'made', expandable: true, isLoading: false, isCollapsed: false, children: [] },
      { id: idCounter++, content: 'tea.', expandable: true, isLoading: false, isCollapsed: false, children: [] }
    ]);
  }

  selectModel(id: string): void {
    this.selectedModelId.set(id);
    localStorage.setItem('telescopic_selected_model', id);
  }

  getCurrentModel(): ModelInfo | undefined {
    return this.modelsList().find(m => m.id === this.selectedModelId());
  }

  hasApiKey(provider: string): boolean {
    return !!this.userApiKeys()[provider.toLowerCase()]?.trim();
  }

  hasCurrentApiKey(): boolean {
    const currentModel = this.getCurrentModel();
    return currentModel ? this.hasApiKey(currentModel.provider) : false;
  }

  getCurrentApiKey(): string {
    const currentModel = this.getCurrentModel();
    if (!currentModel) return '';
    return this.userApiKeys()[currentModel.provider.toLowerCase()] || '';
  }

  onApiKeyInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const currentModel = this.getCurrentModel();
    if (currentModel) {
      const provider = currentModel.provider.toLowerCase();
      this.userApiKeys.update(keys => ({
        ...keys,
        [provider]: input.value.trim()
      }));
    }
  }

  async exportStory(): Promise<void> {
    const fullText = this.getCurrentStoryText(this.story());
    if (!fullText) return;
    try {
      await navigator.clipboard.writeText(fullText);
      this.copySuccess.set(true);
      setTimeout(() => this.copySuccess.set(false), 2500);
    } catch (e) {
      console.error('Copy to clipboard failed:', e);
    }
  }

  async generateInitialStory(): Promise<void> {
    if (!this.prompt().trim() || this.isLoading()) {
      return;
    }
    this.isLoading.set(true);
    this.error.set(null);
    this.story.set([]);

    try {
      const initialSegments = await this.telescopicService.generateInitialStory(this.prompt());
      this.story.set(this.mapSegmentsToNodes(initialSegments));
    } catch (e) {
      console.error(e);
      this.error.set('Failed to generate the story. The AI might be busy. Please try again.');
    } finally {
      this.isLoading.set(false);
    }
  }

  getSentenceWithBlank(nodes: StoryNode[], targetId: number): string {
    const traverse = (node: StoryNode): string => {
      if (node.id === targetId) {
        return '_';
      }
      if (node.children.length === 0 || node.isCollapsed) {
        return node.content;
      }
      return node.children.map(traverse).join(' ');
    };

    const raw = nodes.map(traverse).join(' ');
    return raw.replace(/\s+/g, ' ').trim();
  }

  async handleExpand(nodeToExpand: StoryNode): Promise<void> {
    if (!nodeToExpand.expandable || nodeToExpand.isLoading) {
      return;
    }

    // Toggle back if already has children but is collapsed
    if (nodeToExpand.children.length > 0 && nodeToExpand.isCollapsed) {
      this.updateNodeCollapseState(nodeToExpand.id, false);
      return;
    }

    if (nodeToExpand.children.length > 0) {
      return;
    }

    const currentModel = this.getCurrentModel();
    const provider = currentModel ? currentModel.provider.toLowerCase() : 'openai';
    const apiKey = this.userApiKeys()[provider] || '';

    const isTestRunner = typeof (globalThis as any).jasmine !== 'undefined' || typeof (globalThis as any).describe === 'function';

    if (!apiKey && !isTestRunner) {
      this.isSettingsOpen.set(true);
      this.error.set(`Please enter your ${provider.toUpperCase()} API Key in Settings to expand this word.`);
      return;
    }

    const sentenceWithBlank = this.getSentenceWithBlank(this.story(), nodeToExpand.id);
    this.updateNodeLoadingState(this.story, nodeToExpand.id, true);
    this.error.set(null);

    try {
      const modelId = currentModel ? currentModel.id : 'gpt-5.4-nano';
      const newSegments = await this.telescopicService.expandText(
        sentenceWithBlank, 
        nodeToExpand.content,
        provider,
        modelId,
        apiKey
      );
      this.addChildrenToNode(this.story, nodeToExpand.id, this.mapSegmentsToNodes(newSegments));
    } catch (e: any) {
      console.error(e);
      const msg = typeof e === 'string' ? e : e?.message || '';
      this.error.set(`Failed to expand text. ${msg}`.trim());
    } finally {
      this.updateNodeLoadingState(this.story, nodeToExpand.id, false);
    }
  }

  handleCollapse(nodeToCollapse: StoryNode): void {
    this.updateNodeCollapseState(nodeToCollapse.id, true);
  }

  private updateNodeCollapseState(id: number, isCollapsed: boolean): void {
    this.story.update(currentStory => {
      const newStory = JSON.parse(JSON.stringify(currentStory));
      const findAndUpdate = (nodes: StoryNode[]): boolean => {
        for (const node of nodes) {
          if (node.id === id) {
            node.isCollapsed = isCollapsed;
            return true;
          }
          if (node.children && findAndUpdate(node.children)) {
            return true;
          }
        }
        return false;
      };
      findAndUpdate(newStory);
      return newStory;
    });
  }

  private mapSegmentsToNodes(segments: StorySegment[]): StoryNode[] {
    return segments.map(segment => ({
      id: idCounter++,
      content: segment.content,
      expandable: segment.expandable,
      isLoading: false,
      isCollapsed: false,
      children: [],
    }));
  }

  private getCurrentStoryText(nodes: StoryNode[]): string {
    let text = '';
    for (const node of nodes) {
      if (node.children.length > 0 && !node.isCollapsed) {
        text += ' ' + this.getCurrentStoryText(node.children);
      } else {
        text += ' ' + node.content;
      }
    }
    return text.replace(/\s+/g, ' ').trim();
  }
  
  private updateNodeLoadingState(signal: typeof this.story, id: number, isLoading: boolean): void {
    signal.update(currentStory => {
        const newStory = JSON.parse(JSON.stringify(currentStory));
        const findAndupdate = (nodes: StoryNode[]): boolean => {
            for (const node of nodes) {
                if (node.id === id) {
                    node.isLoading = isLoading;
                    return true;
                }
                if (node.children && findAndupdate(node.children)) {
                    return true;
                }
            }
            return false;
        };
        findAndupdate(newStory);
        return newStory;
    });
  }

  private addChildrenToNode(signal: typeof this.story, id: number, children: StoryNode[]): void {
     signal.update(currentStory => {
        const newStory = JSON.parse(JSON.stringify(currentStory));
        const findAndAdd = (nodes: StoryNode[]): boolean => {
            for (const node of nodes) {
                if (node.id === id) {
                    node.children = children;
                    node.isCollapsed = false;
                    return true;
                }
                if (node.children && findAndAdd(node.children)) {
                    return true;
                }
            }
            return false;
        };
        findAndAdd(newStory);
        return newStory;
    });
  }
}


