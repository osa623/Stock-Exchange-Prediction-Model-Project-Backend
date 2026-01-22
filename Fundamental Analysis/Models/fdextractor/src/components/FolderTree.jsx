import React, { useState } from 'react';

const FolderNode = ({ node, level = 0, onSelect, selectedPath }) => {
    const [isOpen, setIsOpen] = useState(false);
    const isFolder = node.type === 'directory';
    const hasChildren = node.children && node.children.length > 0;

    // Normalize paths for comparison (handle potential root issues)
    const isSelected = selectedPath === node.path || (selectedPath === null && node.path === '');

    const handleClick = (e) => {
        e.stopPropagation();
        if (isFolder) {
            setIsOpen(!isOpen);
        }
        if (onSelect) {
            onSelect(node);
        }
    };

    // Simple file/folder icons 
    const FolderIcon = () => (
        <svg className={`w-5 h-5 text-yellow-500 mr-2 transition-transform ${isOpen ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
    );

    const FileIcon = () => (
        <svg className="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    );

    return (
        <div className="select-none">
            <div
                className={`flex items-center py-1.5 px-2 cursor-pointer rounded-md transition-colors ${level === 0 ? 'font-medium' : ''} ${isSelected ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100'}`}
                style={{ paddingLeft: `${level * 12 + 8}px` }}
                onClick={handleClick}
            >
                {isFolder ? <FolderIcon /> : <FileIcon />}
                <span className={`text-sm truncate ${isSelected ? 'font-semibold' : isFolder ? 'text-gray-700' : 'text-gray-600'}`}>
                    {node.name}
                </span>
            </div>

            {isFolder && isOpen && hasChildren && (
                <div className="ml-1 border-l border-gray-200">
                    {node.children.map((child) => (
                        <FolderNode
                            key={child.path}
                            node={child}
                            level={level + 1}
                            onSelect={onSelect}
                            selectedPath={selectedPath}
                        />
                    ))}
                </div>
            )}

            {isFolder && isOpen && !hasChildren && (
                <div className="pl-8 py-1 text-xs text-gray-400 italic">
                    (Empty)
                </div>
            )}
        </div>
    );
};

const FolderTree = ({ data, title = "Data Explorer", onSelect, selectedPath }) => {
    if (!data) return null;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 h-full flex flex-col overflow-hidden">
            <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 className="font-semibold text-gray-800 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    {title}
                </h3>
                {selectedPath && (
                    <button
                        onClick={() => onSelect(null)}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                        Clear
                    </button>
                )}
            </div>
            <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-200">
                <FolderNode
                    node={data}
                    onSelect={onSelect}
                    selectedPath={selectedPath}
                />
            </div>
        </div>
    );
};

export default FolderTree;
