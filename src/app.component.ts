import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GeminiService, StorySegment } from './services/gemini.service';
import { StoryNodeComponent, StoryNode } from './components/story-node/story-node.component';
import { CommonModule } from '@angular/common';

let idCounter = 0;

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, StoryNodeComponent, CommonModule],
})
export class AppComponent {
  private readonly geminiService = inject(GeminiService);

  prompt = signal<string>('A detective finds a mysterious, glowing key in a rainy alley.');
  story = signal<StoryNode[]>([]);
  isLoading = signal<boolean>(false);
  error = signal<string | null>(null);

  async generateInitialStory(): Promise<void> {
    if (!this.prompt().trim() || this.isLoading()) {
      return;
    }
    this.isLoading.set(true);
    this.error.set(null);
    this.story.set([]);

    try {
      const initialSegments = await this.geminiService.generateInitialStory(this.prompt());
      this.story.set(this.mapSegmentsToNodes(initialSegments));
    } catch (e) {
      console.error(e);
      this.error.set('Failed to generate the story. The AI might be busy. Please try again.');
    } finally {
      this.isLoading.set(false);
    }
  }

  async handleExpand(nodeToExpand: StoryNode): Promise<void> {
    if (!nodeToExpand.expandable || nodeToExpand.isLoading || (nodeToExpand.children && nodeToExpand.children.length > 0)) {
      return;
    }
    const fullContext = this.getCurrentStoryText(this.story());
    
    this.updateNodeLoadingState(this.story, nodeToExpand.id, true);

    try {
      const newSegments = await this.geminiService.expandText(fullContext, nodeToExpand.content);
      this.addChildrenToNode(this.story, nodeToExpand.id, this.mapSegmentsToNodes(newSegments));
    } catch (e) {
      console.error(e);
      this.error.set('Failed to expand the text. Please try again.');
    } finally {
      this.updateNodeLoadingState(this.story, nodeToExpand.id, false);
    }
  }

  private mapSegmentsToNodes(segments: StorySegment[]): StoryNode[] {
    return segments.map(segment => ({
      id: idCounter++,
      content: segment.content,
      expandable: segment.expandable,
      isLoading: false,
      children: [],
    }));
  }

  private getCurrentStoryText(nodes: StoryNode[]): string {
    let text = '';
    for (const node of nodes) {
      text += node.content;
      if (node.children.length > 0) {
        text += ' ' + this.getCurrentStoryText(node.children);
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
