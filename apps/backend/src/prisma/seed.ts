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

    console.log('Global topics seeded.');
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });