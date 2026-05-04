import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { LoginForm } from "../components/LoginForm"
import { hasResumeSessionInSessionStorage } from "@/features/auth/lib/clientSessionResume"

export function LoginPage() {
  const navigate = useNavigate()

  useEffect(() => {
    if (hasResumeSessionInSessionStorage()) {
      navigate("/dashboard", { replace: true })
    }
  }, [navigate])

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-[#f8f9fa] p-4 sm:p-6 antialiased">
      <div className="w-full flex flex-col items-center max-w-lg">
        {/* Logo / Brand Header */}
        <div className="mb-10 flex flex-col items-center space-y-3">
          <div className="h-12 w-12 bg-gradient-to-br from-primary to-primary-hover rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-2xl">M</span>
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold tracking-tight text-foreground" style={{ letterSpacing: "-0.02em" }}>
              Mini ERP
            </h1>
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-medium mt-1">
              Smart Management
            </p>
          </div>
        </div>
        
        {/* Login Form Component (một CTA gửi yêu cầu Owner nằm trong form) */}
        <LoginForm />
      </div>
    </main>
  )
}
