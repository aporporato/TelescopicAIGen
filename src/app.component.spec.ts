import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { GeminiService } from './services/gemini.service';

describe('AppComponent', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let mockGeminiService: jasmine.SpyObj<GeminiService>;

  beforeEach(async () => {
    mockGeminiService = jasmine.createSpyObj('GeminiService', ['generateInitialStory', 'expandText']);

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        { provide: GeminiService, useValue: mockGeminiService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default prompt signal', () => {
    expect(component.prompt()).toContain('detective');
    expect(component.story()).toEqual([]);
    expect(component.isLoading()).toBeFalse();
    expect(component.error()).toBeNull();
  });

  it('should generate initial story successfully', async () => {
    mockGeminiService.generateInitialStory.and.returnValue(Promise.resolve([
      { content: 'Sentence 1', expandable: true },
    ]));

    await component.generateInitialStory();

    expect(component.story().length).toBe(1);
    expect(component.story()[0].content).toBe('Sentence 1');
    expect(component.isLoading()).toBeFalse();
    expect(component.error()).toBeNull();
  });

  it('should handle error when story generation fails', async () => {
    mockGeminiService.generateInitialStory.and.returnValue(Promise.reject('API Error'));

    await component.generateInitialStory();

    expect(component.story()).toEqual([]);
    expect(component.isLoading()).toBeFalse();
    expect(component.error()).toContain('Failed to generate');
  });

  it('should handle text expansion', async () => {
    const targetItem = { id: 1, content: 'Initial text', expandable: true, isLoading: false, children: [] };
    component.story.set([targetItem]);

    mockGeminiService.expandText.and.returnValue(Promise.resolve([
      { content: 'expanded detail', expandable: true }
    ]));

    await component.handleExpand(targetItem);

    expect(mockGeminiService.expandText).toHaveBeenCalled();
  });

  it('should not trigger expand if item is non-expandable or already loading', async () => {
    const nonExpandable = { id: 2, content: 'Static text', expandable: false, isLoading: false, children: [] };
    await component.handleExpand(nonExpandable);
    expect(mockGeminiService.expandText).not.toHaveBeenCalled();

    const loadingItem = { id: 3, content: 'Loading text', expandable: true, isLoading: true, children: [] };
    await component.handleExpand(loadingItem);
    expect(mockGeminiService.expandText).not.toHaveBeenCalled();
  });

  it('should handle expansion failure gracefully', async () => {
    const targetItem = { id: 4, content: 'Failing item', expandable: true, isLoading: false, children: [] };
    component.story.set([targetItem]);

    mockGeminiService.expandText.and.returnValue(Promise.reject('Expansion failed'));

    await component.handleExpand(targetItem);

    expect(targetItem.isLoading).toBeFalse();
    expect(component.error()).toContain('Failed to expand');
  });
});
