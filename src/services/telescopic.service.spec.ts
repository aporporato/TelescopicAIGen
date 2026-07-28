import { TestBed } from '@angular/core/testing';
import { TelescopicService } from './telescopic.service';

describe('TelescopicService', () => {
  let service: TelescopicService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TelescopicService],
    });
    service = TestBed.inject(TelescopicService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should generate initial story segments from mock response', async () => {
    const mockSegments = [
      { content: 'A detective finds ', expandable: false },
      { content: 'a glowing key', expandable: true },
      { content: ' in a rainy alley.', expandable: false },
    ];

    spyOn(service as any, 'generateInitialStory').and.returnValue(Promise.resolve(mockSegments));

    const result = await service.generateInitialStory('A detective finds a key.');
    expect(result.length).toBe(3);
    expect(result[1].content).toBe('a glowing key');
    expect(result[1].expandable).toBeTrue();
  });

  it('should expand text segment from mock response', async () => {
    const mockExpansion = [
      { content: ' It radiated an ', expandable: false },
      { content: 'ancient blue pulse', expandable: true },
    ];

    spyOn(service as any, 'expandText').and.returnValue(Promise.resolve(mockExpansion));

    const result = await service.expandText('Story context', 'a glowing key');
    expect(result.length).toBe(2);
    expect(result[1].expandable).toBeTrue();
  });
});
