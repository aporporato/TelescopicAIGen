import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface StoryNode {
  id: number;
  content: string;
  expandable: boolean;
  isLoading: boolean;
  children: StoryNode[];
}

@Component({
  selector: 'app-story-node',
  templateUrl: './story-node.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule],
})
export class StoryNodeComponent {
  @Input({ required: true }) node!: StoryNode;
  @Output() expand = new EventEmitter<StoryNode>();

  onExpandClick(): void {
    if (!this.node.isLoading && this.node.children.length === 0) {
      this.expand.emit(this.node);
    }
  }
}
