import { DashboardNav } from "@/components/DashboardNav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <DashboardNav />
      <main className="flex-1 px-4 py-6 max-w-5xl mx-auto w-full">{children}</main>
    </>
  );
}
