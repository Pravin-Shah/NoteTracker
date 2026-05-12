import { useState, useEffect } from 'react';
import api from '../../api/client';
import ReactMarkdown from 'react-markdown';
import { Search, Brain, Link as LinkIcon, Clock, ChevronRight } from 'lucide-react';

export default function BrainWiki() {
    const [pages, setPages] = useState<any[]>([]);
    const [selectedPage, setSelectedPage] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchPages();
    }, []);

    const fetchPages = async () => {
        try {
            const response = await api.get('/api/brain/wiki');
            setPages(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching wiki pages:', error);
            setLoading(false);
        }
    };

    const fetchPageDetails = async (title: string) => {
        try {
            const response = await api.get(`/api/brain/wiki/${encodeURIComponent(title)}`);
            setSelectedPage(response.data);
        } catch (error) {
            console.error('Error fetching page details:', error);
        }
    };

    const filteredPages = pages.filter(p => 
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
        p.category?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex flex-1 h-full bg-[#121212] overflow-hidden">
            {/* Wiki List */}
            <div className="w-80 border-r border-gray-800 flex flex-col bg-[#1a1a1a]">
                <div className="p-4 border-b border-gray-800">
                    <div className="flex items-center gap-2 mb-4">
                        <Brain className="w-5 h-5 text-blue-500" />
                        <h2 className="text-lg font-semibold">Brain Wiki</h2>
                    </div>
                    <div className="relative">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Search wiki..."
                            className="w-full bg-[#2a2a2a] border-none rounded-md py-2 pl-10 pr-4 text-sm focus:ring-1 focus:ring-blue-600 outline-none"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>
                
                <div className="flex-1 overflow-y-auto">
                    {loading ? (
                        <div className="p-8 text-center text-gray-500">Loading...</div>
                    ) : filteredPages.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">No pages found.</div>
                    ) : (
                        <div className="flex flex-col">
                            {filteredPages.map(page => (
                                <button
                                    key={page.id}
                                    onClick={() => fetchPageDetails(page.title)}
                                    className={`p-4 text-left border-b border-gray-800/50 transition-colors ${selectedPage?.title === page.title ? 'bg-blue-600/10 border-l-4 border-l-blue-600' : 'hover:bg-[#252525]'}`}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-xs font-medium text-blue-400 uppercase tracking-wider">{page.category}</span>
                                    </div>
                                    <h3 className="font-medium text-gray-100">{page.title}</h3>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto bg-[#121212]">
                {selectedPage ? (
                    <div className="max-w-4xl mx-auto p-8">
                        <div className="flex items-center gap-2 text-xs text-gray-500 mb-6">
                            <span>Second Brain</span>
                            <ChevronRight className="w-3 h-3" />
                            <span>{selectedPage.category}</span>
                            <ChevronRight className="w-3 h-3" />
                            <span className="text-gray-300">{selectedPage.title}</span>
                        </div>

                        <h1 className="text-4xl font-bold mb-4 text-white">{selectedPage.title}</h1>
                        
                        <div className="flex items-center gap-6 text-sm text-gray-500 mb-8 pb-8 border-b border-gray-800">
                            <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                <span>Updated {new Date(selectedPage.last_updated).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <LinkIcon className="w-4 h-4" />
                                <span>{selectedPage.links?.length || 0} connections</span>
                            </div>
                        </div>

                        <div className="prose prose-invert max-w-none prose-blue">
                            <ReactMarkdown>{selectedPage.content}</ReactMarkdown>
                        </div>

                        {/* Connections Section */}
                        {selectedPage.links && selectedPage.links.length > 0 && (
                            <div className="mt-12 pt-8 border-t border-gray-800">
                                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                    <LinkIcon className="w-5 h-5 text-blue-500" />
                                    Related Concepts
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {selectedPage.links.map((link: any, idx: number) => {
                                        const otherId = link.wiki_id_1 === selectedPage.id ? link.wiki_id_2 : link.wiki_id_1;
                                        // Note: We need a way to get the title for otherId
                                        // For now, let's assume the API returns enough info or we can find it in the 'pages' list
                                        const otherPage = pages.find(p => p.id === otherId);
                                        if (!otherPage) return null;

                                        return (
                                            <button
                                                key={idx}
                                                onClick={() => fetchPageDetails(otherPage.title)}
                                                className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-800 hover:border-blue-600/50 transition-all text-left group"
                                            >
                                                <div className="text-xs text-blue-400 mb-1">{link.relationship_type}</div>
                                                <div className="font-medium group-hover:text-blue-400 transition-colors">{otherPage.title}</div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
                        <Brain className="w-16 h-16 text-gray-800" />
                        <div className="text-center">
                            <h3 className="text-xl font-medium text-gray-300">Your Knowledge Graph</h3>
                            <p className="max-w-xs mx-auto">Select a wiki page from the sidebar to explore your second brain.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
