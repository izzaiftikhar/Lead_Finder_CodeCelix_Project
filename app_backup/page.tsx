import { AppCard } from "@/components/ui/AppCard";

export default function Home() {
  return (
    <div className="p-10 flex justify-center bg-gray-50 min-h-screen">
      <div className="w-full max-w-sm">
        <AppCard 
          name="Test Business" 
          address="Lahore" 
          country="Pakistan" 
          whatsappStatus="FOUND" 
          chatbotStatus="NOT_FOUND" 
          leadScore="HIGH" 
        />
      </div>
    </div>
  )
}