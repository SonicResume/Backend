import { NextResponse } from "next/server";
import nodemailer from "nodemailer";

export async function POST(req: Request) {
  try {
    const { name, email, kit } = await req.json();

    if (!email || !kit) {
      return NextResponse.json({ error: "Missing email or kit data" }, { status: 400 });
    }

    // --- SMTP Transport ---
    const transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: Number(process.env.SMTP_PORT) || 587,
      secure: Number(process.env.SMTP_PORT) === 465, // true only for port 465
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
      },
    });

    // --- Plain text email body ---
    const textBody = `
Interview Prep Kit for ${name || "Candidate"}

----------------------------------------
${kit}
----------------------------------------

Generated via ${process.env.NEXT_PUBLIC_SITE_NAME || "SonicResume"}.
© ${new Date().getFullYear()} SonicResume. All rights reserved.
    `;

    // --- Mail options ---
    const mailOptions = {
      from: `"${process.env.NEXT_PUBLIC_SITE_NAME}" <${process.env.CONTACT_FROM}>`,
      to: email,
      subject: "Your Interview Prep Kit",
      text: textBody,
    };

    await transporter.sendMail(mailOptions);

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("❌ Email send error:", error);
    return NextResponse.json({ error: "Failed to send email" }, { status: 500 });
  }
}

