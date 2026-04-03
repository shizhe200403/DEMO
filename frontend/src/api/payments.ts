import http from "./http";

export interface OrderData {
  order_no: string;
  status: "pending" | "paid" | "cancelled" | "refunded";
  plan_type: "monthly" | "annual";
  amount: string;
  pay_url?: string;
  plan_end: string | null;
  created_at: string;
}

export async function createOrder(planType: "monthly" | "annual"): Promise<OrderData> {
  const { data } = await http.post("/payments/orders/create/", { plan_type: planType });
  return data.data as OrderData;
}

export async function getOrder(orderNo: string): Promise<OrderData> {
  const { data } = await http.get(`/payments/orders/${orderNo}/`);
  return data.data as OrderData;
}

export async function getMyOrders(): Promise<OrderData[]> {
  const { data } = await http.get("/payments/orders/");
  return data.data as OrderData[];
}
