import { useQuery } from "@tanstack/react-query";
import { api, Transaction } from "@/lib/api";
import { mockTransactions } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

interface TransactionParams {
  source?: string;
  project?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
  search?: string;
  page?: number;
  limit?: number;
  sort_by?: string;
  order?: "asc" | "desc";
}

export function useTransactions(params: TransactionParams) {
  return useQuery({
    queryKey: ["transactions", params],
    queryFn: async () => {
      if (USE_MOCK) {
        // Simulate API delay
        await new Promise((r) => setTimeout(r, 500));
        
        let filtered = [...mockTransactions];
        
        // Apply filters
        if (params.source) {
          filtered = filtered.filter((t) => t.source === params.source);
        }
        if (params.project) {
          filtered = filtered.filter((t) => t.project === params.project);
        }
        if (params.status) {
          filtered = filtered.filter((t) => t.status === params.status);
        }
        if (params.search) {
          const search = params.search.toLowerCase();
          filtered = filtered.filter(
            (t) =>
              t.client_operation_id?.toLowerCase().includes(search) ||
              t.user_email?.toLowerCase().includes(search) ||
              t.source_id.toLowerCase().includes(search)
          );
        }
        
        // Pagination
        const page = params.page || 1;
        const limit = params.limit || 50;
        const total = filtered.length;
        const start = (page - 1) * limit;
        const end = start + limit;
        
        return {
          data: filtered.slice(start, end),
          meta: {
            page,
            limit,
            total,
            total_pages: Math.ceil(total / limit),
          },
        };
      }
      
      // Real API call - transform backend response to frontend format
      const response = await api.getTransactions(params);
      return {
        data: response.items,
        meta: {
          page: response.page,
          limit: response.limit,
          total: response.total,
          total_pages: response.pages,
        },
      };
    },
    staleTime: 30_000,
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: ["transaction", id],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 300));
        const txn = mockTransactions.find((t) => t.id === id);
        if (!txn) throw new Error("Transaction not found");
        return { data: { ...txn, raw_data: { mock: true } } };
      }
      return api.getTransaction(id);
    },
    enabled: !!id,
  });
}
