import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StoryNodeComponent, StoryNode } from './story-node.component';

describe('StoryNodeComponent', () => {
  let component: StoryNodeComponent;
  let fixture: ComponentFixture<StoryNodeComponent>;

  const mockNode: StoryNode = {
    id: 1,
    content: 'mysterious key',
    expandable: true,
    isLoading: false,
    children: [],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StoryNodeComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(StoryNodeComponent);
    component = fixture.componentInstance;
    component.node = mockNode;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should emit expand event when clicked and expandable', () => {
    spyOn(component.expand, 'emit');
    component.onExpandClick();
    expect(component.expand.emit).toHaveBeenCalledWith(mockNode);
  });

  it('should not emit expand event if node is loading', () => {
    component.node = { ...mockNode, isLoading: true };
    spyOn(component.expand, 'emit');
    component.onExpandClick();
    expect(component.expand.emit).not.toHaveBeenCalled();
  });

  it('should not emit expand event if node already has children', () => {
    component.node = { ...mockNode, children: [mockNode] };
    spyOn(component.expand, 'emit');
    component.onExpandClick();
    expect(component.expand.emit).not.toHaveBeenCalled();
  });
});
