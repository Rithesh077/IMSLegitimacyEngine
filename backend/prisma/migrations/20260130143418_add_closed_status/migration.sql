-- CreateEnum
CREATE TYPE "Role" AS ENUM ('FACULTY', 'CORPORATE', 'PLACEMENT', 'STUDENT');

-- CreateEnum
CREATE TYPE "InternshipStatus" AS ENUM ('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CLOSED');

-- CreateEnum
CREATE TYPE "LocationType" AS ENUM ('REMOTE', 'ONSITE', 'HYBRID');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "role" "Role" NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "corporate_profiles" (
    "id" TEXT NOT NULL,
    "company_name" TEXT NOT NULL,
    "hr_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,

    CONSTRAINT "corporate_profiles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "departments" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,

    CONSTRAINT "departments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "internships" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "status" "InternshipStatus" NOT NULL DEFAULT 'DRAFT',
    "department_id" TEXT NOT NULL,
    "location_type" "LocationType" NOT NULL,
    "is_paid" BOOLEAN NOT NULL,
    "stipend" TEXT,
    "duration" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "corporate_id" TEXT NOT NULL,
    "creator_id" TEXT,

    CONSTRAINT "internships_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "corporate_profiles_user_id_key" ON "corporate_profiles"("user_id");

-- CreateIndex
CREATE UNIQUE INDEX "departments_name_key" ON "departments"("name");

-- AddForeignKey
ALTER TABLE "corporate_profiles" ADD CONSTRAINT "corporate_profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "internships" ADD CONSTRAINT "internships_department_id_fkey" FOREIGN KEY ("department_id") REFERENCES "departments"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "internships" ADD CONSTRAINT "internships_corporate_id_fkey" FOREIGN KEY ("corporate_id") REFERENCES "corporate_profiles"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "internships" ADD CONSTRAINT "internships_creator_id_fkey" FOREIGN KEY ("creator_id") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;
