export type Status = "yes" | "no" | "unknown" | "unreachable";

export type Lead = {
  name: string;
  address: string;
  country: string;
  industry: string;
  phone: string;
  website: string;
  whatsapp: Status;
  whatsapp_source: string;
  whatsapp_number: string;
  chatbot: Status;
  chatbot_vendors: string[];
  score: number;
};

export type SearchParams = {
  country: string;
  city: string;
  industry: string;
  limit: number;
  only_with_website: boolean;
};

export type Filters = {
  bestOnly: boolean; // has website and no chatbot
  whatsappOnly: boolean;
  sort: "score" | "name";
};
