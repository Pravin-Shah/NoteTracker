import { useState, useEffect } from 'react';
import api from '../../api/client';
import ReactMarkdown from 'react-markdown';
import { Search, Brain, Link as LinkIcon, Clock, ExternalLink, Trash2 } from 'lucide-react';

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

    const handleDeletePage = async () => {
        if (!selectedPage) return;
        if (!confirm(`Are you sure you want to delete "${selectedPage.title}"?`)) return;

        try {
            await api.delete(`/api/brain/wiki/${selectedPage.id}`);
            setSelectedPage(null);
            fetchPages();
        } catch (error) {
            console.error('Error deleting page:', error);
            alert('Failed to delete page');
        }
    };

    const filteredPages = pages.filter(p => 
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
        p.category?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex flex-1 h-full bg-[#121212] overflow-hidden">
            {/* Wiki List - Match Sidebar/Feed style */}
            <div className="w-80 border-r border-gray-800 flex flex-col bg-[#1a1a1a]">
                <div className="px-4 py-6 border-b border-gray-800">
                    <div className="flex items-center gap-2 mb-4 px-2">
                        <Brain className="w-5 h-5 text-blue-500" />
                        <h2 className="text-lg font-semibold text-white">Brain Wiki</h2>
                    </div>
                    <div className="relative px-2">
                        <Search className="w-4 h-4 absolute left-5 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Search wiki..."
                            className="w-full bg-[#2a2a2a] border border-gray-700 rounded-md py-2 pl-10 pr-4 text-[13px] text-gray-200 focus:ring-1 focus:ring-blue-600 outline-none transition-all"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>
                
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {loading ? (
                        <div className="p-8 text-center text-gray-500 text-sm">Loading...</div>
                    ) : filteredPages.length === 0 ? (
                        <div className="p-8 text-center text-gray-500 text-sm">No pages found.</div>
                    ) : (
                        <div className="flex flex-col">
                            {/* Grouped by Category */}
                            {Array.from(new Set(filteredPages.map(p => p.category))).map(cat => (
                                <div key={cat} className="mb-2">
                                    <div className="px-6 py-2 text-[11px] font-bold text-gray-500 uppercase tracking-widest bg-[#151515]">
                                        {cat || 'Uncategorized'}
                                    </div>
                                    {filteredPages.filter(p => p.category === cat).map(page => (
                                        <button
                                            key={page.id}
                                            onClick={() => fetchPageDetails(page.title)}
                                            className={`w-full p-4 text-left border-b border-gray-800/30 transition-all ${selectedPage?.title === page.title ? 'bg-[#2a2a2a] text-white border-l-4 border-l-blue-600' : 'text-gray-400 hover:bg-[#202020] hover:text-gray-200'}`}
                                        >
                                            <h3 className="text-[14px] font-medium">{page.title}</h3>
                                        </button>
                                    ))}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Content Area - Match NoteEditor style */}
            <div className="flex-1 flex flex-col bg-[#252525] overflow-hidden">
                {selectedPage ? (
                    <>
                        {/* Header - Matching NoteEditor Header */}
                        <div className="bg-[#1e1e1e] border-b border-gray-800 px-8 py-5 flex items-center justify-between flex-shrink-0">
                            <div className="flex items-center gap-2 text-[13px]" style={{ paddingTop: '0.5rem', paddingBottom: '0.5rem' }}>
                                <span className="text-gray-500">Second Brain</span>
                                <span className="text-gray-600 mx-2">/</span>
                                <span className="text-gray-500">{selectedPage.category}</span>
                                <span className="text-gray-600 mx-2">/</span>
                                <span className="text-white font-medium">{selectedPage.title}</span>
                            </div>
                            
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={handleDeletePage}
                                    className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                                    title="Delete wiki page"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-[12px] font-medium rounded transition-colors flex items-center gap-2">
                                    <ExternalLink className="w-3 h-3" />
                                    Explore Connections
                                </button>
                            </div>
                        </div>

                        {/* Scrollable Content Container */}
                        <div className="flex-1 overflow-y-auto">
                            <div className="max-w-3xl mx-auto py-10" style={{ paddingLeft: '3rem', paddingRight: '2rem' }}>
                                {/* Title */}
                                <h1 className="text-2xl font-semibold text-white leading-tight" style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>
                                    {selectedPage.title}
                                </h1>

                                {/* Metadata - Match Note Metadata Style */}
                                <div className="flex items-center gap-6 text-[13px] text-gray-500 border-b border-gray-700" style={{ paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4" />
                                        <span>Updated: {new Date(selectedPage.last_updated).toLocaleDateString()}</span>
                                    </div>
                                    <span className="text-gray-700">|</span>
                                    <div className="flex items-center gap-2">
                                        <LinkIcon className="w-4 h-4" />
                                        <span>Connections: {selectedPage.links?.length || 0}</span>
                                    </div>
                                </div>

                                {/* White Content Card - MATCHING USER SCREENSHOT */}
                                <div className="bg-white rounded-xl p-8 shadow-2xl mb-12 min-h-[400px]">
                                    <div className="prose prose-slate max-w-none prose-p:text-gray-700 prose-headings:text-gray-900 text-gray-800 leading-relaxed">
                                        <ReactMarkdown>{selectedPage.content}</ReactMarkdown>
                                    </div>
                                </div>

                                {/* Related Concepts Section - Premium Styling */}
                                {selectedPage.links && selectedPage.links.length > 0 && (
                                    <div className="mt-8 pt-8 border-t border-gray-800">
                                        <h3 className="text-[13px] font-medium text-gray-400 uppercase tracking-widest mb-6">Related Concepts</h3>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            {selectedPage.links.map((link: any, idx: number) => {
                                                const otherId = link.wiki_id_1 === selectedPage.id ? link.wiki_id_2 : link.wiki_id_1;
                                                const otherPage = pages.find(p => p.id === otherId);
                                                if (!otherPage) return null;

                                                return (
                                                    <button
                                                        key={idx}
                                                        onClick={() => fetchPageDetails(otherPage.title)}
                                                        className="group p-4 bg-[#1a1a1a] rounded-lg border border-gray-800 hover:border-blue-600/50 hover:bg-[#202020] transition-all text-left"
                                                    >
                                                        <div className="text-[10px] text-blue-500 uppercase font-bold tracking-tighter mb-1 opacity-80 group-hover:opacity-100 transition-opacity">
                                                            {link.relationship_type}
                                                        </div>
                                                        <div className="text-[14px] font-medium text-gray-200 group-hover:text-white transition-colors">
                                                            {otherPage.title}
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 space-y-6">
                        <div className="w-24 h-24 bg-[#1e1e1e] rounded-full flex items-center justify-center border border-gray-800">
                            <Brain className="w-12 h-12 text-gray-700" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-xl font-medium text-gray-300 mb-2">Knowledge Graph</h3>
                            <p className="max-w-xs mx-auto text-sm">Select a wiki page from the sidebar to explore your second brain.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
