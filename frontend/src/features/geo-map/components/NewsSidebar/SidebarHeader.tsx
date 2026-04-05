interface Country {
  iso_code: string;
  name: string;
  name_de?: string;
  region?: string;
  article_count_24h?: number;
  article_count_7d?: number;
}

interface Props {
  country: Country | null | undefined;
  isLoading: boolean;
  onClose: () => void;
}

export function SidebarHeader({ country, isLoading, onClose }: Props) {
  return (
    <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
      <div>
        {isLoading ? (
          <div className="h-6 w-32 bg-gray-200 animate-pulse rounded" />
        ) : country ? (
          <>
            <h2 className="text-lg font-semibold text-gray-900">
              {country.name_de || country.name}
            </h2>
            <p className="text-sm text-gray-500">
              {country.region} - {country.article_count_24h || 0} articles today
            </p>
          </>
        ) : (
          <p className="text-gray-500">Select a country</p>
        )}
      </div>
      <button
        onClick={onClose}
        className="p-1 rounded-full hover:bg-gray-200 transition-colors"
        aria-label="Close sidebar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
