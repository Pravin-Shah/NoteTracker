import { LeftPane } from './LeftPane';
import { FeedPane } from './FeedPane';
import { EditorPane } from './EditorPane';

export function AppLayout() {
  return (
    <div className="flex h-screen w-full overflow-hidden">
      <LeftPane />
      <FeedPane />
      <EditorPane />
    </div>
  );
}
