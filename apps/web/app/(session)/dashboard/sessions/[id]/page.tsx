import { SessionFlowPage } from "@/components/session/SessionFlowPage";

export default async function SessionPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    return <SessionFlowPage sessionId={id} />;
}
