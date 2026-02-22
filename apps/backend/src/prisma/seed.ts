import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
    const topics = [
        { name: 'React' },
        { name: 'Node.js' },
        { name: 'JavaScript' },
        { name: 'System Design' },
        { name: 'PostgreSQL' },
    ];

    for (const topic of topics) {
        await prisma.topic.upsert({
            where: {
                name_isGlobal: {
                    name: topic.name,
                    isGlobal: true,
                },
            },
            update: {},
            create: {
                name: topic.name,
                isGlobal: true,
            },
        });
    }

    const skills = [
        { name: 'Frontend (React/Next.js)' },
        { name: 'Backend (Node.js/NestJS)' },
        { name: 'System Design & Architecture' },
        { name: 'Database Design (SQL/NoSQL)' },
        { name: 'Cloud & DevOps (AWS/GCP)' },
        { name: 'Behavioral & Leadership' },
        { name: 'Data Structures & Algorithms' },
        { name: 'Python Engineering' },
        { name: 'Mobile (React Native/Flutter)' },
        { name: 'Testing & QA' },
    ];

    for (const skill of skills) {
        await prisma.skillTag.upsert({
            where: { name: skill.name },
            update: {},
            create: {
                name: skill.name,
                isGlobal: true,
            },
        });
    }

    console.log('Global topics and skill tags seeded.');
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });