export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  graphql_public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      graphql: {
        Args: {
          extensions?: Json
          operationName?: string
          query?: string
          variables?: Json
        }
        Returns: Json
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
  public: {
    Tables: {
      audit_log: {
        Row: {
          action: string
          actor_id: string | null
          at: string
          id: number
          row_id: string | null
          table_name: string
        }
        Insert: {
          action: string
          actor_id?: string | null
          at?: string
          id?: never
          row_id?: string | null
          table_name: string
        }
        Update: {
          action?: string
          actor_id?: string | null
          at?: string
          id?: never
          row_id?: string | null
          table_name?: string
        }
        Relationships: []
      }
      declarations: {
        Row: {
          confidence: number | null
          extractor: string
          field: string
          height_mm: number | null
          id: string
          image_id: string | null
          scan_id: string
          value: string
          width_height_ratio: number | null
          word_ids: number[]
        }
        Insert: {
          confidence?: number | null
          extractor?: string
          field: string
          height_mm?: number | null
          id?: string
          image_id?: string | null
          scan_id: string
          value: string
          width_height_ratio?: number | null
          word_ids?: number[]
        }
        Update: {
          confidence?: number | null
          extractor?: string
          field?: string
          height_mm?: number | null
          id?: string
          image_id?: string | null
          scan_id?: string
          value?: string
          width_height_ratio?: number | null
          word_ids?: number[]
        }
        Relationships: [
          {
            foreignKeyName: "declarations_image_id_fkey"
            columns: ["image_id"]
            isOneToOne: false
            referencedRelation: "scan_images"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "declarations_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "declarations_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
      evidence: {
        Row: {
          created_at: string
          created_by: string
          id: string
          note: string | null
          scan_id: string
          storage_path: string | null
        }
        Insert: {
          created_at?: string
          created_by: string
          id?: string
          note?: string | null
          scan_id: string
          storage_path?: string | null
        }
        Update: {
          created_at?: string
          created_by?: string
          id?: string
          note?: string | null
          scan_id?: string
          storage_path?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "evidence_created_by_fkey"
            columns: ["created_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "evidence_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "evidence_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
      model_calls: {
        Row: {
          at: string
          id: string
          input_tokens: number | null
          latency_ms: number | null
          model: string
          output: Json | null
          output_tokens: number | null
          prompt_hash: string | null
          scan_id: string | null
        }
        Insert: {
          at?: string
          id?: string
          input_tokens?: number | null
          latency_ms?: number | null
          model: string
          output?: Json | null
          output_tokens?: number | null
          prompt_hash?: string | null
          scan_id?: string | null
        }
        Update: {
          at?: string
          id?: string
          input_tokens?: number | null
          latency_ms?: number | null
          model?: string
          output?: Json | null
          output_tokens?: number | null
          prompt_hash?: string | null
          scan_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "model_calls_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "model_calls_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
      ocr_words: {
        Row: {
          confidence: number
          h: number
          id: number
          image_id: string
          scan_id: string
          text: string
          w: number
          x: number
          y: number
        }
        Insert: {
          confidence: number
          h: number
          id?: never
          image_id: string
          scan_id: string
          text: string
          w: number
          x: number
          y: number
        }
        Update: {
          confidence?: number
          h?: number
          id?: never
          image_id?: string
          scan_id?: string
          text?: string
          w?: number
          x?: number
          y?: number
        }
        Relationships: [
          {
            foreignKeyName: "ocr_words_image_id_fkey"
            columns: ["image_id"]
            isOneToOne: false
            referencedRelation: "scan_images"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ocr_words_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ocr_words_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
      products: {
        Row: {
          barcode: string | null
          brand: string | null
          category: string | null
          created_at: string
          created_by: string | null
          id: string
          manufacturer: string | null
          match_key: string | null
          name: string
        }
        Insert: {
          barcode?: string | null
          brand?: string | null
          category?: string | null
          created_at?: string
          created_by?: string | null
          id?: string
          manufacturer?: string | null
          match_key?: string | null
          name: string
        }
        Update: {
          barcode?: string | null
          brand?: string | null
          category?: string | null
          created_at?: string
          created_by?: string | null
          id?: string
          manufacturer?: string | null
          match_key?: string | null
          name?: string
        }
        Relationships: [
          {
            foreignKeyName: "products_created_by_fkey"
            columns: ["created_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          created_at: string
          full_name: string | null
          id: string
          role: string
        }
        Insert: {
          created_at?: string
          full_name?: string | null
          id: string
          role?: string
        }
        Update: {
          created_at?: string
          full_name?: string | null
          id?: string
          role?: string
        }
        Relationships: []
      }
      reports: {
        Row: {
          created_at: string
          docx_path: string | null
          id: string
          json_path: string | null
          pdf_path: string | null
          scan_id: string
        }
        Insert: {
          created_at?: string
          docx_path?: string | null
          id?: string
          json_path?: string | null
          pdf_path?: string | null
          scan_id: string
        }
        Update: {
          created_at?: string
          docx_path?: string | null
          id?: string
          json_path?: string | null
          pdf_path?: string | null
          scan_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "reports_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "reports_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
      scan_images: {
        Row: {
          created_at: string
          height: number | null
          id: string
          kind: string
          scan_id: string
          storage_path: string
          width: number | null
        }
        Insert: {
          created_at?: string
          height?: number | null
          id?: string
          kind?: string
          scan_id: string
          storage_path: string
          width?: number | null
        }
        Update: {
          created_at?: string
          height?: number | null
          id?: string
          kind?: string
          scan_id?: string
          storage_path?: string
          width?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "scan_images_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scan_images_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
      scans: {
        Row: {
          compliance_score: number | null
          created_at: string
          error: string | null
          finished_at: string | null
          has_reference_card: boolean
          id: string
          inspector_id: string
          location: string | null
          mm_per_px: number | null
          notes: string | null
          pdp_height_mm: number | null
          pdp_width_mm: number | null
          product_id: string | null
          source: string
          status: string
        }
        Insert: {
          compliance_score?: number | null
          created_at?: string
          error?: string | null
          finished_at?: string | null
          has_reference_card?: boolean
          id?: string
          inspector_id: string
          location?: string | null
          mm_per_px?: number | null
          notes?: string | null
          pdp_height_mm?: number | null
          pdp_width_mm?: number | null
          product_id?: string | null
          source?: string
          status?: string
        }
        Update: {
          compliance_score?: number | null
          created_at?: string
          error?: string | null
          finished_at?: string | null
          has_reference_card?: boolean
          id?: string
          inspector_id?: string
          location?: string | null
          mm_per_px?: number | null
          notes?: string | null
          pdp_height_mm?: number | null
          pdp_width_mm?: number | null
          product_id?: string | null
          source?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "scans_inspector_id_fkey"
            columns: ["inspector_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scans_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
        ]
      }
      violations: {
        Row: {
          confidence: number | null
          evidence: Json
          id: string
          message: string
          rule_id: string
          rule_ref: string
          scan_id: string
          severity: string
        }
        Insert: {
          confidence?: number | null
          evidence?: Json
          id?: string
          message: string
          rule_id: string
          rule_ref: string
          scan_id: string
          severity: string
        }
        Update: {
          confidence?: number | null
          evidence?: Json
          id?: string
          message?: string
          rule_id?: string
          rule_ref?: string
          scan_id?: string
          severity?: string
        }
        Relationships: [
          {
            foreignKeyName: "violations_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scan_search"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "violations_scan_id_fkey"
            columns: ["scan_id"]
            isOneToOne: false
            referencedRelation: "scans"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      dashboard_summary: {
        Row: {
          avg_score: number | null
          scans_compliant: number | null
          scans_done: number | null
          scans_failed: number | null
          scans_this_week: number | null
        }
        Relationships: []
      }
      scan_search: {
        Row: {
          compliance_score: number | null
          created_at: string | null
          finished_at: string | null
          id: string | null
          inspector_id: string | null
          inspector_name: string | null
          location: string | null
          product_brand: string | null
          product_id: string | null
          product_manufacturer: string | null
          product_name: string | null
          search: string | null
          source: string | null
          status: string | null
        }
        Relationships: [
          {
            foreignKeyName: "scans_inspector_id_fkey"
            columns: ["inspector_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scans_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
        ]
      }
      top_violations: {
        Row: {
          count: number | null
          rule_id: string | null
          rule_ref: string | null
          severity: string | null
        }
        Relationships: []
      }
      violations_by_category: {
        Row: {
          category: string | null
          count: number | null
          severity: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      auth_role: { Args: never; Returns: string }
      claim_scan: {
        Args: never
        Returns: {
          compliance_score: number | null
          created_at: string
          error: string | null
          finished_at: string | null
          has_reference_card: boolean
          id: string
          inspector_id: string
          location: string | null
          mm_per_px: number | null
          notes: string | null
          pdp_height_mm: number | null
          pdp_width_mm: number | null
          product_id: string | null
          source: string
          status: string
        }[]
        SetofOptions: {
          from: "*"
          to: "scans"
          isOneToOne: false
          isSetofReturn: true
        }
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  graphql_public: {
    Enums: {},
  },
  public: {
    Enums: {},
  },
} as const
