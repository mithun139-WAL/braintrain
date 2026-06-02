import {
    BarChart3,
    Brain,
    Briefcase,
    Dumbbell,
    LayoutDashboard,
    Layers,
    MessageCircle,
    Settings,
    Database,
    type LucideIcon,
} from "lucide-react";

export interface DashboardNavItem {
    name: string;
    href: string;
    icon: LucideIcon;
    description: string;
    matches?: (pathname: string) => boolean;
}

export interface DashboardNavSection {
    label: string;
    items: DashboardNavItem[];
}

export const START_SESSION_HREF = "/dashboard/sessions/start";

export const dashboardNavigation: DashboardNavSection[] = [
    {
        label: "Guide",
        items: [
            {
                name: "Home",
                href: "/dashboard",
                icon: LayoutDashboard,
                description: "Readiness, momentum, and the next best action.",
                matches: (pathname) => pathname === "/dashboard",
            },
            {
                name: "Practice",
                href: "/dashboard/sessions",
                icon: Brain,
                description: "Run sessions, review attempts, and reopen reports.",
                matches: (pathname) => pathname.startsWith("/dashboard/sessions") && !pathname.includes("/interview-journey"),
            },
            {
                name: "Journeys",
                href: "/dashboard/interview-journey",
                icon: Briefcase,
                description: "Simulate full hiring pipelines with dynamic rounds.",
                matches: (pathname) => pathname.startsWith("/dashboard/interview-journey"),
            },
            {
                name: "Insights",
                href: "/dashboard/analytics",
                icon: BarChart3,
                description: "Understand performance patterns and weak signals.",
                matches: (pathname) =>
                    pathname.startsWith("/dashboard/analytics") ||
                    pathname.startsWith("/dashboard/progress") ||
                    pathname.startsWith("/dashboard/trends"),
            },
            {
                name: "Coach",
                href: "/dashboard/coach",
                icon: MessageCircle,
                description: "Have a focused conversation with your AI mentor.",
                matches: (pathname) => pathname.startsWith("/dashboard/coach"),
            },
        ],
    },
    {
        label: "Build",
        items: [
            {
                name: "Topics",
                href: "/dashboard/topics",
                icon: Layers,
                description: "Organize the domains you want to practice deeply.",
                matches: (pathname) => pathname.startsWith("/dashboard/topics"),
            },
            {
                name: "Plan",
                href: "/dashboard/training",
                icon: Dumbbell,
                description: "Follow adaptive drills generated from your sessions.",
                matches: (pathname) => pathname.startsWith("/dashboard/training"),
            },
            {
                name: "Knowledge",
                href: "/dashboard/knowledge",
                icon: Database,
                description: "Manage interviewer personas, RAG documents, and profile optimizations.",
                matches: (pathname) => pathname.startsWith("/dashboard/knowledge"),
            },
        ],
    },
    {
        label: "Account",
        items: [
            {
                name: "Settings",
                href: "/dashboard/settings",
                icon: Settings,
                description: "Profile, preferences, and subscription controls.",
                matches: (pathname) => pathname.startsWith("/dashboard/settings"),
            },
        ],
    },
    {
        label: "Admin",
        items: [],
    },
];

interface DashboardContext {
    eyebrow: string;
    title: string;
    description: string;
    activeHref: string;
}

const dashboardContexts: Array<{
    matches: (pathname: string) => boolean;
    context: DashboardContext;
}> = [
    {
        matches: (pathname) => pathname === "/dashboard",
        context: {
            eyebrow: "Mentor Home",
            title: "Overview",
            description: "Your current readiness, momentum, and next best move.",
            activeHref: "/dashboard",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/sessions/start"),
        context: {
            eyebrow: "Practice Builder",
            title: "Create Session",
            description: "Shape the interview format, challenge level, and goal before you begin.",
            activeHref: "/dashboard/sessions",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/sessions"),
        context: {
            eyebrow: "Practice Workspace",
            title: "Sessions",
            description: "Run focused drills, review attempts, and revisit session outcomes.",
            activeHref: "/dashboard/sessions",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/analytics"),
        context: {
            eyebrow: "Insight Mode",
            title: "Insights",
            description: "Patterns, deltas, and the signals the AI coach wants you to act on.",
            activeHref: "/dashboard/analytics",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/progress"),
        context: {
            eyebrow: "Insight Mode",
            title: "Progress",
            description: "A deeper breakdown of skill movement across recent sessions.",
            activeHref: "/dashboard/analytics",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/trends"),
        context: {
            eyebrow: "Insight Mode",
            title: "Trends",
            description: "Longer-range signals and sustained performance movement.",
            activeHref: "/dashboard/analytics",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/coach"),
        context: {
            eyebrow: "Coach Workspace",
            title: "AI Coach",
            description: "A focused conversation designed to turn weak signals into deliberate practice.",
            activeHref: "/dashboard/coach",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/topics/") || pathname === "/dashboard/topics",
        context: {
            eyebrow: "Knowledge Map",
            title: "Topics",
            description: "Track how each topic performs and decide where to practice next.",
            activeHref: "/dashboard/topics",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/training"),
        context: {
            eyebrow: "Adaptive Plan",
            title: "Training Plan",
            description: "Daily drills generated from your latest performance patterns.",
            activeHref: "/dashboard/training",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/settings"),
        context: {
            eyebrow: "Account",
            title: "Settings",
            description: "Profile controls, learning preferences, and subscription details.",
            activeHref: "/dashboard/settings",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/interview-journey/new"),
        context: {
            eyebrow: "Hiring Simulation",
            title: "New Journey",
            description: "Upload a resume and paste a job description to start.",
            activeHref: "/dashboard/interview-journey",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/interview-journey") && pathname.includes("/analysis"),
        context: {
            eyebrow: "Hiring Simulation",
            title: "Journey Analysis",
            description: "AI-generated hiring plan based on your resume and job description.",
            activeHref: "/dashboard/interview-journey",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/interview-journey") && pathname.includes("/rounds"),
        context: {
            eyebrow: "Hiring Simulation",
            title: "Interview Rounds",
            description: "Select and launch each round of your interview journey.",
            activeHref: "/dashboard/interview-journey",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/interview-journey") && pathname.includes("/report"),
        context: {
            eyebrow: "Hiring Simulation",
            title: "Final Report",
            description: "Recruiter-style hiring report across all rounds.",
            activeHref: "/dashboard/interview-journey",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/interview-journey") && pathname !== "/dashboard/interview-journey/new",
        context: {
            eyebrow: "Hiring Simulation",
            title: "Interview Journey",
            description: "Full hiring pipeline simulation.",
            activeHref: "/dashboard/interview-journey",
        },
    },
    {
        matches: (pathname) => pathname.startsWith("/dashboard/knowledge"),
        context: {
            eyebrow: "Knowledge Hub",
            title: "Knowledge & Career Optimizer",
            description: "Interviewer personas, RAG references, and profile transition optimization tools.",
            activeHref: "/dashboard/knowledge",
        },
    },
];

export function resolveDashboardContext(pathname: string): DashboardContext {
    return (
        dashboardContexts.find((entry) => entry.matches(pathname))?.context ?? {
            eyebrow: "Workspace",
            title: "Dashboard",
            description: "Your AI-native practice environment.",
            activeHref: "/dashboard",
        }
    );
}

export function isDashboardItemActive(item: DashboardNavItem, pathname: string) {
    return item.matches ? item.matches(pathname) : pathname === item.href;
}
