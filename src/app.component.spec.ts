import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { TelescopicService } from './services/telescopic.service';

describe('AppComponent', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let mockTelescopicService: jasmine.SpyObj<TelescopicService>;

  beforeEach(async () => {
    mockTelescopicService = jasmine.createSpyObj('TelescopicService', ['generateInitialStory', 'expandText']);

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        { provide: TelescopicService, useValue: mockTelescopicService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default prompt signal and reset story to trigger nodes', () => {
    expect(component.prompt()).toContain('detective');
    component.resetStory();
    expect(component.story().length).toBe(3);
    expect(component.story()[0].content).toBe('I');
    expect(component.story()[0].expandable).toBeTrue();
    expect(component.story()[2].content).toBe('tea.');
    expect(component.story()[2].expandable).toBeTrue();
    expect(component.isLoading()).toBeFalse();
    expect(component.error()).toBeNull();
  });

  it('should compute sentence_with_blank correctly for targeted word node', () => {
    const nodes = [
      { id: 10, content: 'I', expandable: true, isLoading: false, children: [] },
      { id: 11, content: 'made', expandable: true, isLoading: false, children: [] },
      { id: 12, content: 'tea.', expandable: true, isLoading: false, children: [] }
    ];
    component.story.set(nodes);

    const sentenceWithBlank = component.getSentenceWithBlank(nodes, 12);
    expect(sentenceWithBlank).toBe('I made _');
  });

  it('should generate initial story successfully', async () => {
    mockTelescopicService.generateInitialStory.and.returnValue(Promise.resolve([
      { content: 'Sentence 1', expandable: true },
    ]));

    await component.generateInitialStory();

    expect(component.story().length).toBe(1);
    expect(component.story()[0].content).toBe('Sentence 1');
    expect(component.isLoading()).toBeFalse();
    expect(component.error()).toBeNull();
  });

  it('should handle error when story generation fails', async () => {
    mockTelescopicService.generateInitialStory.and.returnValue(Promise.reject('API Error'));

    await component.generateInitialStory();

    expect(component.story()).toEqual([]);
    expect(component.isLoading()).toBeFalse();
    expect(component.error()).toContain('Failed to generate');
  });

  it('should handle text expansion and pass sentence_with_blank with placeholder', async () => {
    const targetItem = { id: 1, content: 'tea.', expandable: true, isLoading: false, children: [] };
    const storyNodes = [
      { id: 100, content: 'I', expandable: true, isLoading: false, children: [] },
      { id: 101, content: 'made', expandable: true, isLoading: false, children: [] },
      targetItem
    ];
    component.story.set(storyNodes);

    mockTelescopicService.expandText.and.returnValue(Promise.resolve([
      { content: 'steeped herbal tea', expandable: true }
    ]));

    await component.handleExpand(targetItem);

    expect(mockTelescopicService.expandText).toHaveBeenCalledWith('I made _', 'tea.', 'openai', 'gpt-5.4-nano', '');
  });

  it('should handle collapse and re-expansion toggling', () => {
    const childNode = { id: 2, content: 'steeped', expandable: false, isLoading: false, children: [] };
    const parentNode = { id: 1, content: 'tea.', expandable: true, isLoading: false, isCollapsed: false, children: [childNode] };
    component.story.set([parentNode]);

    // Test collapse
    component.handleCollapse(parentNode);
    expect(component.story()[0].isCollapsed).toBeTrue();

    // Test re-expand toggles collapse to false without calling API
    component.handleExpand(component.story()[0]);
    expect(component.story()[0].isCollapsed).toBeFalse();
    expect(mockTelescopicService.expandText).not.toHaveBeenCalled();
  });

  it('should manage model settings and API keys', () => {
    expect(component.modelsList().length).toBeGreaterThanOrEqual(1);
    expect(component.isSettingsOpen()).toBeFalse();

    component.toggleSettings();
    expect(component.isSettingsOpen()).toBeTrue();

    component.selectModel('gemini-3.5-flash');
    expect(component.selectedModelId()).toBe('gemini-3.5-flash');

    const fakeEvent = { target: { value: 'test-key-123' } } as any;
    component.onApiKeyInput(fakeEvent);
    expect(component.hasApiKey('google')).toBeTrue();
  });

  it('should not trigger expand if item is non-expandable or already loading', async () => {
    const nonExpandable = { id: 2, content: 'Static text', expandable: false, isLoading: false, children: [] };
    await component.handleExpand(nonExpandable);
    expect(mockTelescopicService.expandText).not.toHaveBeenCalled();

    const loadingItem = { id: 3, content: 'Loading text', expandable: true, isLoading: true, children: [] };
    await component.handleExpand(loadingItem);
    expect(mockTelescopicService.expandText).not.toHaveBeenCalled();
  });

  it('should handle expansion failure gracefully', async () => {
    const targetItem = { id: 4, content: 'Failing item', expandable: true, isLoading: false, children: [] };
    component.story.set([targetItem]);

    mockTelescopicService.expandText.and.returnValue(Promise.reject('Expansion failed'));

    await component.handleExpand(targetItem);

    expect(targetItem.isLoading).toBeFalse();
    expect(component.error()).toContain('Failed to expand');
  });
});

