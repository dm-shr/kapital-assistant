import ClientOnly from "@/components/client-only"
import ChatInterface from "./chat-interface"
import { initialMessages } from "./initial-messages"
import { FaGithub, FaLinkedin } from "react-icons/fa"

export default function Page() {
  return (
    <main className="container mx-auto max-w-2xl min-h-screen p-2 sm:p-4 flex flex-col bg-gray-50">
      <div className="mb-3 sm:mb-4 text-center">
        <h1 className="text-xl sm:text-2xl font-bold mb-1 sm:mb-2">Kapital Assistant</h1>
        <h2 className="text-base sm:text-lg text-gray-700 mb-2 sm:mb-4">AI-powered interface for exploring financial documentation</h2>

        <p className="text-xs sm:text-sm text-gray-600 mb-2">Interested? Let's stay in touch!</p>
        <div className="flex justify-center space-x-4 mb-2">
          <a
            href="https://github.com/dm-shr"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-900 hover:text-black flex items-center gap-2"
          >
            <FaGithub className="text-xl" />
            <span className="hidden md:inline">GitHub</span>
          </a>
          <a
            href="https://www.linkedin.com/in/dshiriaev/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 flex items-center gap-2"
          >
            <FaLinkedin className="text-xl" />
            <span className="hidden md:inline">LinkedIn</span>
          </a>
        </div>
      </div>

      <ClientOnly>
        <ChatInterface initialMessages={initialMessages} />
      </ClientOnly>

      <div className="mt-4 text-center text-sm text-gray-600">
        <span className="font-medium">Made by: </span>
        <a
          href="https://www.linkedin.com/in/author1/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800"
        >
          Dmitrii Shiriaev
        </a>
        <span className="mx-1">•</span>
        <a
          href="https://www.linkedin.com/in/author2/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800"
        >
          Aleksdandr Perevalov
        </a>
        <span className="mx-1">•</span>
        <a
          href="https://www.linkedin.com/in/author3/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800"
        >
          Vladislav Raskoshinskii
        </a>
        <span className="mx-1">•</span>
        <a
          href="https://www.linkedin.com/in/author4/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800"
        >
          Ilya Moshonkin
        </a>
      </div>
    </main>
  )
}
