import { redirect } from "next/navigation";

export default function MerchantPage() {
  redirect("/home?app_entrance=login");
}
