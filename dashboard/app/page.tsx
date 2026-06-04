import Dashboard from "./Dashboard";
import { loadRegression, loadRun, loadRunV2 } from "@/lib/data";

export default function Page() {
  return <Dashboard v1={loadRun()} v2={loadRunV2()} reg={loadRegression()} />;
}
